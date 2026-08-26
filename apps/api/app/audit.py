"""Functional audit — run with API deps available: python -m app.audit

Tests core manager + payment gates + sample seed without a live browser.
Does not print secrets. Exit code 0 = pass.
"""
from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.db import SessionLocal
from app.main import app
from app.models import AuditLog, Client, Invoice, Project
from app.seed import ensure_samples


PASS = 0
FAIL = 0


def ok(name: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {name}")


def bad(name: str, detail: str = "") -> None:
    global FAIL
    FAIL += 1
    print(f"  FAIL  {name}" + (f" — {detail}" if detail else ""))


async def run() -> int:
    print("CFS Designers — functional audit")
    print("=" * 50)

    await ensure_samples()

    async with SessionLocal() as db:
        nc = (await db.execute(select(func.count()).select_from(Client).where(Client.name.like("%SAMPLE%")))).scalar()
        np = (await db.execute(select(func.count()).select_from(Project).where(Project.name.like("SAMPLE%")))).scalar()
        ni = (await db.execute(select(func.count()).select_from(Invoice).where(Invoice.number.like("SAMPLE%")))).scalar()
        if nc and nc >= 2 and np and np >= 2 and ni and ni >= 3:
            ok(f"Sample data present (clients={nc} projects={np} invoices={ni})")
        else:
            bad("Sample data", f"clients={nc} projects={np} invoices={ni}")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        h = await client.get("/api/v1/health")
        if h.status_code == 200 and h.json().get("report_version") == "phase5-complete":
            ok("Health report_version=phase5-complete")
        else:
            bad("Health", str(h.text)[:120])

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@cfsdesigners.com", "password": "Admin123!"},
        )
        if login.status_code != 200 or "access_token" not in login.json():
            bad("Manager login", login.text[:160])
            print("\nStopped — cannot continue without login.")
            return 1
        ok("Manager login")
        token = login.json()["access_token"]
        hdr = {"Authorization": f"Bearer {token}"}

        for path, label in [
            ("/api/v1/live", "Live board"),
            ("/api/v1/employees", "Employees list"),
            ("/api/v1/clients", "Clients list"),
            ("/api/v1/projects", "Projects list"),
            ("/api/v1/invoices", "Invoices list"),
        ]:
            r = await client.get(path, headers=hdr)
            if r.status_code == 200:
                ok(label)
            else:
                bad(label, f"HTTP {r.status_code}")

        projects = (await client.get("/api/v1/projects", headers=hdr)).json()
        harbour = next((p for p in projects if "Harbour" in (p.get("name") or "")), None)
        summit = next((p for p in projects if "Iliff" in (p.get("name") or "")), None)

        if harbour and harbour.get("gate") == "need_deposit":
            ok("Harbour shows need_deposit while unpaid in Intake")
        else:
            bad("Harbour gate badge", str(harbour.get("gate") if harbour else "missing"))

        if harbour:
            blocked = await client.patch(
                f"/api/v1/projects/{harbour['id']}",
                headers=hdr,
                json={
                    "name": harbour["name"],
                    "client_id": harbour.get("client_id"),
                    "work_scope": harbour.get("work_scope") or "",
                    "assignee_id": harbour.get("assignee_id"),
                    "area_sqft": harbour.get("area_sqft"),
                    "storeys": harbour.get("storeys"),
                    "phase": "preliminary_design",
                    "work_state": harbour.get("work_state") or "waiting",
                    "comments": harbour.get("comments") or "",
                    "due_at": harbour.get("due_at"),
                    "target_at": harbour.get("target_at"),
                    "contract_value": harbour.get("contract_value") or 0,
                    "deposit_pct": harbour.get("deposit_pct") or 50,
                    "currency": harbour.get("currency") or "USD",
                },
            )
            if blocked.status_code == 409:
                ok("Harbour cannot leave Intake unpaid (409)")
            else:
                bad("Harbour Intake gate", f"HTTP {blocked.status_code} {blocked.text[:100]}")

        if summit:
            # Ensure sample balance is unpaid — manual testing may have marked it Paid
            async with SessionLocal() as db:
                bal = (
                    await db.execute(select(Invoice).where(Invoice.number == "SAMPLE-INV-1002"))
                ).scalar_one_or_none()
                if bal and bal.status == "paid":
                    bal.status = "pending"
                    await db.commit()
                proj = await db.get(Project, summit["id"])
                if proj and proj.phase in ("stamped_drawings", "field_files", "run_files"):
                    proj.phase = "preliminary_design"
                    await db.commit()
            # Refresh project row after reset
            projects = (await client.get("/api/v1/projects", headers=hdr)).json()
            summit = next((p for p in projects if "Iliff" in (p.get("name") or "")), summit)

            blocked2 = await client.patch(
                f"/api/v1/projects/{summit['id']}",
                headers=hdr,
                json={
                    "name": summit["name"],
                    "client_id": summit.get("client_id"),
                    "work_scope": summit.get("work_scope") or "",
                    "assignee_id": summit.get("assignee_id"),
                    "area_sqft": summit.get("area_sqft"),
                    "storeys": summit.get("storeys"),
                    "phase": "stamped_drawings",
                    "work_state": summit.get("work_state") or "working",
                    "comments": summit.get("comments") or "",
                    "due_at": summit.get("due_at"),
                    "target_at": summit.get("target_at"),
                    "contract_value": summit.get("contract_value") or 0,
                    "deposit_pct": summit.get("deposit_pct") or 50,
                    "currency": summit.get("currency") or "USD",
                },
            )
            if blocked2.status_code == 409:
                ok("Summit cannot enter Stamped Drawings with balance unpaid (409)")
            else:
                bad("Summit release gate", f"HTTP {blocked2.status_code}")

        invoices = (await client.get("/api/v1/invoices", headers=hdr)).json()
        delayed = [i for i in invoices if i.get("number") == "SAMPLE-INV-2001"]
        if delayed and int(delayed[0].get("delayed_days") or 0) > 0:
            ok(f"Harbour deposit delayed_days={delayed[0]['delayed_days']}")
        else:
            bad("Delayed days on SAMPLE-INV-2001")

        xlsx = await client.get("/api/v1/reports/payments.xlsx", headers=hdr)
        if xlsx.status_code == 200 and len(xlsx.content) > 100:
            ok("Payments Excel export")
        else:
            bad("Payments Excel", f"HTTP {xlsx.status_code}")

        emps = (await client.get("/api/v1/employees", headers=hdr)).json()
        staff = [e for e in emps if e.get("role") == "employee"]
        if staff:
            emp_id = staff[0]["id"]
            day = datetime.utcnow().strftime("%Y-%m-%d")
            day_r = await client.get(f"/api/v1/employees/{emp_id}/day?date={day}", headers=hdr)
            if day_r.status_code == 200:
                ok("Day detail endpoint")
            else:
                bad("Day detail", f"HTTP {day_r.status_code}")
            pdf = await client.get(f"/api/v1/employees/{emp_id}/day.pdf?date={day}", headers=hdr)
            if pdf.status_code == 200 and pdf.headers.get("content-type", "").startswith("application/pdf"):
                ok("Day PDF")
            else:
                bad("Day PDF", f"HTTP {pdf.status_code}")
            att = await client.get(f"/api/v1/reports/attendance.csv?date={day}", headers=hdr)
            if att.status_code == 200:
                ok("Attendance CSV")
            else:
                bad("Attendance CSV", f"HTTP {att.status_code}")
            now = datetime.utcnow()
            mon = await client.get(
                f"/api/v1/reports/monthly.pdf?year={now.year}&month={now.month}",
                headers=hdr,
            )
            if mon.status_code == 200:
                ok("Monthly PDF")
            else:
                bad("Monthly PDF", f"HTTP {mon.status_code}")
        else:
            bad("No employee rows for day/PDF tests")

        # Screenshot audit must stay opt-in (no row required if no shots)
        async with SessionLocal() as db:
            before = (
                await db.execute(
                    select(func.count()).select_from(AuditLog).where(AuditLog.action == "screenshot_view")
                )
            ).scalar() or 0
        # Hit file endpoint without audit=1 — count must not rise even for 404
        await client.get("/api/v1/screenshots/00000000-0000-0000-0000-000000000000/file", headers=hdr)
        async with SessionLocal() as db:
            after = (
                await db.execute(
                    select(func.count()).select_from(AuditLog).where(AuditLog.action == "screenshot_view")
                )
            ).scalar() or 0
        if after == before:
            ok("Screenshot file without audit=1 does not write audit")
        else:
            bad("Screenshot audit spam", f"before={before} after={after}")

        # Create project in non-intake without pay → 409
        clients = (await client.get("/api/v1/clients", headers=hdr)).json()
        cid = clients[0]["id"] if clients else None
        if cid:
            create_bad = await client.post(
                "/api/v1/projects",
                headers=hdr,
                json={
                    "name": f"AUDIT TEMP {datetime.utcnow().timestamp():.0f}",
                    "client_id": cid,
                    "phase": "preliminary_design",
                    "work_state": "working",
                    "contract_value": 1000,
                    "deposit_pct": 50,
                    "currency": "USD",
                },
            )
            if create_bad.status_code == 409:
                ok("Create unpaid non-Intake project blocked (409)")
            else:
                bad("Create gate", f"HTTP {create_bad.status_code}")

        create_ok = await client.post(
            "/api/v1/projects",
            headers=hdr,
            json={
                "name": f"AUDIT INTAKE {datetime.utcnow().timestamp():.0f}",
                "client_id": cid,
                "phase": "intake",
                "work_state": "waiting",
                "contract_value": 500,
                "deposit_pct": 50,
                "currency": "USD",
            },
        )
        if create_ok.status_code == 200:
            ok("Create Intake project allowed")
            # cleanup soft: leave it — named AUDIT INTAKE for visibility
        else:
            bad("Create Intake", f"HTTP {create_ok.status_code}")

    print("=" * 50)
    print(f"Result: {PASS} passed, {FAIL} failed")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
