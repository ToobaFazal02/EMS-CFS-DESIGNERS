"""Seed admin + sample employees + demo projects/invoices."""
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from app.auth import create_device_token, hash_password, hash_token
from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.models import Client, Device, Employee, Invoice, Project, Role
from app.services.schema_patch import ensure_sqlite_columns


async def _seed_flow_samples(db, assignee: Employee | None) -> None:
    """Two fictional jobs so the office can see deposit vs unpaid gates."""
    settings = get_settings()
    skip = settings.data_path / ".skip_flow_samples"
    if skip.exists() or not settings.auto_seed_samples:
        print("Flow SAMPLE projects skipped (cleared for client testing / auto_seed_samples=false).")
        return

    existing = (await db.execute(select(Client).where(Client.name == "Summit LGS (SAMPLE)"))).scalar_one_or_none()
    if existing:
        print("Sample clients already present (Summit LGS / Harbour Frames).")
        return

    now = datetime.utcnow()
    c1 = Client(name="Summit LGS (SAMPLE)", location="USA", notes="Training sample — 50% deposit already paid.")
    c2 = Client(name="Harbour Frames (SAMPLE)", location="Australia", notes="Training sample — deposit still pending.")
    db.add_all([c1, c2])
    await db.flush()

    p1 = Project(
        name="SAMPLE — 1027 Iliff St Residence",
        client_id=c1.id,
        work_scope="LGS detailing / preliminary engineering",
        assignee_id=assignee.id if assignee else None,
        area_sqft=2400,
        storeys=2,
        phase="preliminary_design",
        work_state="working",
        comments="Deposit received. Safe to work.",
        due_at=now + timedelta(days=10),
        target_at=now + timedelta(days=21),
        contract_value=10000,
        deposit_pct=50,
        currency="USD",
    )
    p2 = Project(
        name="SAMPLE — Harbour Warehouse Shed",
        client_id=c2.id,
        work_scope="Cold-formed steel shop drawings",
        assignee_id=assignee.id if assignee else None,
        area_sqft=18000,
        storeys=1,
        phase="intake",
        work_state="waiting",
        comments="Do not start until 50% is marked Paid.",
        due_at=now + timedelta(days=2),
        target_at=now + timedelta(days=30),
        contract_value=8000,
        deposit_pct=50,
        currency="USD",
    )
    db.add_all([p1, p2])
    await db.flush()

    db.add_all(
        [
            Invoice(
                client_id=c1.id,
                project_id=p1.id,
                number="SAMPLE-INV-1001",
                amount=5000,
                currency="USD",
                invoice_date=now - timedelta(days=5),
                follow_up_at=now - timedelta(days=1),
                status="paid",
                kind="deposit",
                client_comments="Wire received. SAMPLE only.",
            ),
            Invoice(
                client_id=c1.id,
                project_id=p1.id,
                number="SAMPLE-INV-1002",
                amount=5000,
                currency="USD",
                invoice_date=now,
                follow_up_at=now + timedelta(days=14),
                status="pending",
                kind="balance",
                client_comments="Due before stamped / field / run files.",
            ),
            Invoice(
                client_id=c2.id,
                project_id=p2.id,
                number="SAMPLE-INV-2001",
                amount=4000,
                currency="USD",
                invoice_date=now - timedelta(days=8),
                follow_up_at=now - timedelta(days=3),
                status="pending",
                kind="deposit",
                client_comments="Waiting on advance. Delayed days should be > 0.",
            ),
        ]
    )
    print("Seeded SAMPLE flow: Summit LGS (paid 50%) + Harbour Frames (unpaid, stuck in Intake).")


async def _ensure_admin_and_staff(db) -> Employee | None:
    """Idempotent admin + sample staff. Does NOT reset passwords on every start."""
    admin = (await db.execute(select(Employee).where(Employee.code == "ADMIN"))).scalar_one_or_none()
    if not admin:
        admin = Employee(
            code="ADMIN",
            full_name="CFS Admin",
            email="admin@cfsdesigners.com",
            password_hash=hash_password("Admin123!"),
            role=Role.admin,
        )
        db.add(admin)
    else:
        if not admin.email:
            admin.email = "admin@cfsdesigners.com"
        if not admin.password_hash:
            admin.password_hash = hash_password("Admin123!")
        if admin.role not in (Role.admin, Role.manager):
            admin.role = Role.admin

    samples = [
        ("101", "Waheed Ullah", "waheed@cfsdesigners.com"),
        ("102", "Rohail", "rohail@cfsdesigners.com"),
        ("103", "Waseem", "waseem@cfsdesigners.com"),
        ("104", "Waleed", "waleed@cfsdesigners.com"),
    ]
    demo_emp = None
    for code, name, email in samples:
        emp = (await db.execute(select(Employee).where(Employee.code == code))).scalar_one_or_none()
        if not emp:
            emp = Employee(
                code=code,
                full_name=name,
                email=email,
                password_hash=hash_password("Emp123!"),
                role=Role.employee,
            )
            db.add(emp)
            await db.flush()
        else:
            if not emp.email:
                emp.email = email
            if not emp.password_hash:
                emp.password_hash = hash_password("Emp123!")
        if code == "101":
            demo_emp = emp
    return demo_emp


async def ensure_samples() -> None:
    """Idempotent: API startup — admin login + SAMPLE projects/invoices always present."""
    settings = get_settings()
    settings.data_path
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(ensure_sqlite_columns)
    async with SessionLocal() as db:
        demo_emp = await _ensure_admin_and_staff(db)
        await db.commit()
        await _seed_flow_samples(db, demo_emp)
        await db.commit()


async def main() -> None:
    settings = get_settings()
    settings.data_path
    env = Path(__file__).resolve().parents[1] / ".env"
    example = Path(__file__).resolve().parents[1] / ".env.example"
    if not env.exists() and example.exists():
        env.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(ensure_sqlite_columns)

    async with SessionLocal() as db:
        demo_emp = await _ensure_admin_and_staff(db)
        await db.commit()
        if demo_emp:
            await db.refresh(demo_emp)
            devices = list(
                (
                    await db.execute(
                        select(Device).where(Device.employee_id == demo_emp.id, Device.enrolled_at.is_not(None))
                    )
                ).scalars().all()
            )
            if not devices:
                device = Device(employee_id=demo_emp.id, hostname="DEV-PC", token_hash="pending")
                db.add(device)
                await db.flush()
                token = create_device_token(device.id)
                device.token_hash = hash_token(token)
                device.enrolled_at = datetime.utcnow()
                await db.commit()
                token_path = settings.data_path / "demo_device_token.txt"
                token_path.write_text(token, encoding="utf-8")
                print("Demo device token written to:", token_path)
            else:
                device = devices[0]
                token = create_device_token(device.id)
                device.token_hash = hash_token(token)
                await db.commit()
                token_path = settings.data_path / "demo_device_token.txt"
                token_path.write_text(token, encoding="utf-8")
                print("Demo device token refreshed:", token_path)

        await db.commit()
        await _seed_flow_samples(db, demo_emp)
        await db.commit()
        print("Seed OK. Admin: admin@cfsdesigners.com / Admin123!  |  Staff web: waheed@cfsdesigners.com / Emp123!")


if __name__ == "__main__":
    asyncio.run(main())
