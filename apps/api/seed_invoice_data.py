"""Seed realistic invoice test data for edge-case testing."""

import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select

from app.auth import hash_password
from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.models import Client, Employee, Invoice, InvoiceSettings, Project, Role
from app.services.invoice_settings import DEFAULT_INVOICE_SETTINGS

settings = get_settings()


async def seed_invoice_test_data():
    """Seed comprehensive invoice test data with edge cases."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with SessionLocal() as db:
        # Get or create admin
        admin = (await db.execute(
            select(Employee).where(
                (Employee.email == "admin@example.com") | (Employee.code == "ADMIN")
            )
        )).scalar_one_or_none()
        if not admin:
            admin = Employee(
                code="ADMIN",
                full_name="Admin User",
                email="admin@example.com",
                password_hash=hash_password("admin123"),
                role=Role.admin,
            )
            db.add(admin)
            await db.flush()
            print("✅ Created admin user")
        
        # Seed invoice settings
        tpl = (await db.execute(select(InvoiceSettings).where(InvoiceSettings.id == "default"))).scalar_one_or_none()
        if not tpl:
            tpl = InvoiceSettings(id="default", **DEFAULT_INVOICE_SETTINGS)
            db.add(tpl)
            await db.flush()
        
        # Check if test clients already exist
        existing = (await db.execute(select(Client).where(Client.name == "CYDNEY SKEENS"))).scalar_one_or_none()
        if existing:
            print("Test data already exists — skipping seed")
            return
        
        now = datetime.utcnow()
        
        # Real clients from reference data
        clients_data = [
            {"name": "CYDNEY SKEENS", "location": "USA", "phone": "+1 (214) 763-0146"},
            {"name": "Tooba Fazil", "location": "USA", "phone": "+92 332 4222160"},
            {"name": "Summit LGS Inc.", "location": "Australia", "phone": "+61 2 9876 5432"},
            {"name": "Harbour Steel Frames", "location": "USA", "phone": "+1 (555) 123-4567"},
            {"name": "Urban LGS Solutions", "location": "Canada", "phone": "+1 (416) 555-0199"},
        ]
        
        clients = []
        for c_data in clients_data:
            c = Client(**c_data)
            db.add(c)
            clients.append(c)
        await db.flush()
        
        # Projects with realistic names
        projects_data = [
            {"name": "Powder Coat Booth Project", "client_idx": 0, "area": 309, "rate": 0.4},
            {"name": "wall cartridge project for Keyence", "client_idx": 0, "area": 55, "rate": 10.0},
            {"name": "ROG Puerto Vallarta Project", "client_idx": 1, "area": 1355, "rate": 0.1},
            {"name": "Co vherd Structure", "client_idx": 1, "area": 805, "rate": 0.2},
            {"name": "Casita", "client_idx": 1, "area": 1246, "rate": 0.1},
            {"name": "Container House", "client_idx": 2, "area": 1840, "rate": 0.2},
            {"name": "Modern Floor Plan + Add Stairs", "client_idx": 2, "area": 1, "rate": 50.0},
        ]
        
        projects = []
        for p_data in projects_data:
            client = clients[p_data["client_idx"]]
            p = Project(
                name=p_data["name"],
                client_id=client.id,
                work_scope="LGS Detailing",
                assignee_id=admin.id,
                area_sqft=p_data["area"],
                storeys=1,
                phase="preliminary_design",
                work_state="working",
                contract_value=p_data["area"] * p_data["rate"],
                currency="USD",
            )
            db.add(p)
            projects.append(p)
        await db.flush()
        
        # Invoices with edge cases
        invoices_data = [
            {
                "client_idx": 0,
                "project_idx": 0,
                "number": "INV-2026-001",
                "line_items": [
                    {"description": "Powder Coat Booth Project", "qty": 1, "unit_price": 123.60},
                    {"description": "wall cartridge project for Keyence - 5$ for small panel", "qty": 1, "unit_price": 175.00},
                ],
                "status": "paid",
                "date_offset": -30,
            },
            {
                "client_idx": 1,
                "project_idx": 2,
                "number": "INV-2026-002",
                "line_items": [
                    {"description": "ROG Puerto Vallarta Project - Estimation", "qty": 1355, "unit_price": 0.1},
                    {"description": "Co vherd Structure - Detailing", "qty": 805, "unit_price": 0.2},
                    {"description": "Casita - Estimation", "qty": 1246, "unit_price": 0.1},
                ],
                "status": "pending",
                "date_offset": -5,
            },
            {
                "client_idx": 2,
                "project_idx": 5,
                "number": "INV-2026-003",
                "line_items": [
                    {"description": "Container House - Detailing (ONLY TRUSSES)", "qty": 1840, "unit_price": 0.2},
                    {"description": "Modern Floor Plan + Add Stairs - Estimation (LumpSum)", "qty": 1, "unit_price": 50.00},
                ],
                "status": "sent",
                "date_offset": -15,
            },
            {
                "client_idx": 3,
                "project_idx": None,
                "number": "INV-2026-004",
                "line_items": [
                    {"description": "LGS Framing Design - Phase 1", "qty": 2400, "unit_price": 0.15},
                    {"description": "Engineering Review", "qty": 1, "unit_price": 500.00},
                ],
                "status": "overdue",
                "date_offset": -60,
            },
            {
                "client_idx": 4,
                "project_idx": None,
                "number": "INV-2026-005",
                "line_items": [
                    {"description": "Cold-Formed Steel Detailing", "qty": 3200, "unit_price": 0.12},
                    {"description": "Preliminary Engineering", "qty": 1, "unit_price": 800.00},
                    {"description": "Rush Fee (2-day turnaround)", "qty": 1, "unit_price": 300.00},
                ],
                "status": "proforma",
                "date_offset": 5,
            },
        ]
        
        for inv_data in invoices_data:
            client = clients[inv_data["client_idx"]]
            proj = projects[inv_data["project_idx"]] if inv_data["project_idx"] is not None else None
            
            import json
            amount = sum(item["qty"] * item["unit_price"] for item in inv_data["line_items"])
            
            inv = Invoice(
                client_id=client.id,
                project_id=proj.id if proj else None,
                number=inv_data["number"],
                amount=round(amount, 2),
                currency="USD",
                invoice_date=now + timedelta(days=inv_data["date_offset"]),
                follow_up_at=now + timedelta(days=inv_data["date_offset"] + 14),
                status=inv_data["status"],
                kind="deposit",
                bill_to_name=client.name,
                bill_to_location=client.location,
                bill_to_phone=client.phone or "",
                line_items=json.dumps(inv_data["line_items"]),
                invoice_notes="",
                client_comments="",
            )
            db.add(inv)
        
        await db.commit()
        print("✅ Invoice test data seeded successfully!")
        print(f"   - {len(clients)} clients")
        print(f"   - {len(projects)} projects")
        print(f"   - {len(invoices_data)} invoices (various statuses & edge cases)")


if __name__ == "__main__":
    asyncio.run(seed_invoice_test_data())
