"""Remove SAMPLE / AUDIT demo rows so the office can do final client testing on a clean board.

Keeps real staff + admin logins. Removes:
- Clients / projects / invoices whose names/numbers contain SAMPLE
- Projects whose names start with AUDIT (audit leftovers)

Usage (API venv):
  python -m app.clear_samples
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import or_, select

from app.config import get_settings
from app.db import SessionLocal, engine
from app.models import Base, Client, Invoice, Project
from app.services.schema_patch import ensure_sqlite_columns


async def clear_samples() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(ensure_sqlite_columns)

    async with SessionLocal() as db:
        sample_projects = (
            await db.execute(
                select(Project).where(
                    or_(
                        Project.name.like("SAMPLE%"),
                        Project.name.like("AUDIT%"),
                    )
                )
            )
        ).scalars().all()
        sample_ids = [p.id for p in sample_projects]

        inv_filters = [Invoice.number.like("SAMPLE%")]
        if sample_ids:
            inv_filters.append(Invoice.project_id.in_(sample_ids))
        inv_q = await db.execute(select(Invoice).where(or_(*inv_filters)))
        invs = list(inv_q.scalars().all())
        for inv in invs:
            await db.delete(inv)

        for p in sample_projects:
            await db.delete(p)

        clients = (
            await db.execute(select(Client).where(Client.name.like("%SAMPLE%")))
        ).scalars().all()
        for c in clients:
            leftover = (
                await db.execute(select(Invoice).where(Invoice.client_id == c.id))
            ).scalars().all()
            for inv in leftover:
                await db.delete(inv)
            leftover_p = (
                await db.execute(select(Project).where(Project.client_id == c.id))
            ).scalars().all()
            for p in leftover_p:
                await db.delete(p)
            await db.delete(c)

        await db.commit()
        marker = get_settings().data_path / ".skip_flow_samples"
        marker.write_text("cleared for client testing\n", encoding="utf-8")
        print("Cleared SAMPLE/AUDIT demo data.")
        print(f"  Projects removed: {len(sample_projects)}")
        print(f"  Invoices removed: {len(invs)}")
        print(f"  Clients removed:  {len(clients)}")
        print(f"  Marker written:   {marker}")
        print("Admin + staff logins kept. SAMPLE will NOT auto-return on API restart.")
        print("Add real clients/projects from the web UI for final testing.")


if __name__ == "__main__":
    asyncio.run(clear_samples())
