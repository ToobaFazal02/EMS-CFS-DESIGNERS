"""Isolated demo catalog — fictional names only. Never real CFS client/staff/invoice data."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select

from app.auth import hash_password
from app.config import get_settings
from app.models import Client, Employee, ExpenseCategory, OfficeExpense, Project, Role


async def ensure_demo_catalog(db) -> None:
    """Idempotent demo login + sample board/expenses. Fictional names only."""
    settings = get_settings()

    demo = (await db.execute(select(Employee).where(Employee.code == "DEMO"))).scalar_one_or_none()
    # Auto-create demo login only outside production (or when samples allowed)
    if not demo and (settings.auto_seed_samples or not settings.is_production):
        demo = Employee(
            code="DEMO",
            full_name="Demo Tour",
            email="demo@cfsdesigners.com",
            password_hash=hash_password("DemoTour123!"),
            role=Role.demo,
            is_demo=True,
        )
        db.add(demo)
        await db.flush()
    elif demo:
        demo.role = Role.demo
        demo.is_demo = True
        if not demo.email:
            demo.email = "demo@cfsdesigners.com"
        if not demo.password_hash and (settings.auto_seed_samples or not settings.is_production):
            demo.password_hash = hash_password("DemoTour123!")

    # If no DEMO code yet (prod without auto-seed), still allow catalog when any demo role exists
    if not demo:
        demo = (await db.execute(select(Employee).where(Employee.role == Role.demo))).scalar_one_or_none()
    if not demo and settings.is_production and not settings.auto_seed_samples:
        return

    # Fake staff faces for demo dashboard roster only (no agent enroll)
    for code, name in (("D101", "Alex Sample"), ("D102", "Jordan Sample")):
        emp = (await db.execute(select(Employee).where(Employee.code == code))).scalar_one_or_none()
        if not emp:
            db.add(
                Employee(
                    code=code,
                    full_name=name,
                    email=f"{code.lower()}@demo.local",
                    password_hash=None,
                    role=Role.employee,
                    is_demo=True,
                )
            )

    existing = (
        await db.execute(select(Client).where(Client.name == "Northwind Frames (DEMO)", Client.is_demo == True))  # noqa: E712
    ).scalar_one_or_none()
    if existing:
        return

    now = datetime.utcnow()
    c1 = Client(
        name="Northwind Frames (DEMO)",
        location="USA",
        phone="",
        notes="Fictional demo client — not a real CFS job.",
        is_demo=True,
    )
    c2 = Client(
        name="Pacific LGS (DEMO)",
        location="Australia",
        phone="",
        notes="Fictional demo client — not a real CFS job.",
        is_demo=True,
    )
    db.add_all([c1, c2])
    await db.flush()

    actor_id = demo.id if demo else None
    db.add_all(
        [
            Project(
                name="DEMO — 88 Oak Ave Residence",
                client_id=c1.id,
                work_scope="LGS detailing (sample)",
                area_sqft=2100,
                storeys=2,
                phase="preliminary_design",
                work_state="working",
                comments="Sample board card only.",
                due_at=now + timedelta(days=14),
                target_at=now + timedelta(days=28),
                contract_value=0,
                deposit_pct=50,
                currency="USD",
                is_demo=True,
            ),
            Project(
                name="DEMO — Riverview Shop Shed",
                client_id=c2.id,
                work_scope="Shop drawings (sample)",
                area_sqft=9000,
                storeys=1,
                phase="intake",
                work_state="waiting",
                comments="Sample intake card.",
                due_at=now + timedelta(days=7),
                target_at=now + timedelta(days=40),
                contract_value=0,
                deposit_pct=50,
                currency="USD",
                is_demo=True,
            ),
            OfficeExpense(
                spent_on=datetime(now.year, now.month, 1),
                category=ExpenseCategory.tea_water.value,
                amount_pkr=4500,
                vendor_note="DEMO — office tea (sample)",
                is_demo=True,
                created_by_id=actor_id,
            ),
            OfficeExpense(
                spent_on=datetime(now.year, now.month, min(5, max(now.day, 1))),
                category=ExpenseCategory.electricity.value,
                amount_pkr=28000,
                vendor_note="DEMO — utility bill (sample)",
                is_demo=True,
                created_by_id=actor_id,
            ),
        ]
    )
    print("Seeded isolated DEMO catalog (demo@cfsdesigners.com / DemoTour123!).")
