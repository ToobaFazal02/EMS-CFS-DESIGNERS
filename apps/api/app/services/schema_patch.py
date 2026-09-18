"""SQLite-safe extra columns (create_all does not ALTER existing tables)."""

from __future__ import annotations

import uuid

from sqlalchemy import text


PROJECT_COLS = {
    "contract_value": "FLOAT DEFAULT 0",
    "deposit_pct": "FLOAT DEFAULT 50",
    "currency": "VARCHAR(8) DEFAULT 'USD'",
    "is_demo": "BOOLEAN DEFAULT 0",
    "code": "VARCHAR(32) DEFAULT ''",
}

CLIENT_COLS = {
    "phone": "VARCHAR(40) DEFAULT ''",
    "is_demo": "BOOLEAN DEFAULT 0",
    "initial": "VARCHAR(8) DEFAULT ''",
    "invoice_status": "VARCHAR(24) DEFAULT 'none'",
}

INVOICE_COLS = {
    "bill_to_name": "VARCHAR(120) DEFAULT ''",
    "bill_to_location": "VARCHAR(200) DEFAULT ''",
    "bill_to_phone": "VARCHAR(40) DEFAULT ''",
    "line_items": "TEXT DEFAULT '[]'",
    "invoice_notes": "TEXT DEFAULT ''",
    "invoice_prep": "VARCHAR(24) DEFAULT 'unprepared'",
    "is_demo": "BOOLEAN DEFAULT 0",
}

EMPLOYEE_COLS = {
    "is_demo": "BOOLEAN DEFAULT 0",
}

EXPENSE_COLS = {
    "is_demo": "BOOLEAN DEFAULT 0",
    "receipt_path": "VARCHAR(500) DEFAULT ''",
}

INVOICE_SETTINGS_COLS = {
    "header_color": "VARCHAR(20) DEFAULT '#548235'",
    "highlight_color": "VARCHAR(20) DEFAULT '#c9a227'",
}

PROJECT_ASSIGNEE_COLS = {
    "role": "VARCHAR(20) DEFAULT ''",
}


def _patch_table(sync_conn, table: str, cols: dict[str, str]) -> None:
    rows = sync_conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    if not rows:
        return
    existing = {r[1] for r in rows}
    for name, ddl in cols.items():
        if name not in existing:
            sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def _migrate_assignee_roles(sync_conn) -> None:
    """Legacy rows → one detailer + one engineer per project (runs only while roles blank)."""
    rows = sync_conn.execute(text("PRAGMA table_info(project_assignees)")).fetchall()
    if not rows or "role" not in {r[1] for r in rows}:
        return
    blank = sync_conn.execute(
        text("SELECT COUNT(*) FROM project_assignees WHERE role IS NULL OR TRIM(role) = ''")
    ).scalar()
    if not blank:
        return
    projects = sync_conn.execute(text("SELECT DISTINCT project_id FROM project_assignees")).fetchall()
    for (pid,) in projects:
        members = sync_conn.execute(
            text(
                "SELECT id, employee_id, is_lead, created_at FROM project_assignees "
                "WHERE project_id = :pid ORDER BY is_lead DESC, created_at ASC"
            ),
            {"pid": pid},
        ).fetchall()
        if not members:
            continue
        detailer_emp = members[0][1]
        engineer_emp = members[1][1] if len(members) > 1 else detailer_emp
        sync_conn.execute(text("DELETE FROM project_assignees WHERE project_id = :pid"), {"pid": pid})
        sync_conn.execute(
            text(
                "INSERT INTO project_assignees (id, project_id, employee_id, role, is_lead, created_at) "
                "VALUES (:id, :pid, :eid, 'detailer', 1, CURRENT_TIMESTAMP)"
            ),
            {"id": str(uuid.uuid4()), "pid": pid, "eid": detailer_emp},
        )
        sync_conn.execute(
            text(
                "INSERT INTO project_assignees (id, project_id, employee_id, role, is_lead, created_at) "
                "VALUES (:id, :pid, :eid, 'engineer', 0, CURRENT_TIMESTAMP)"
            ),
            {"id": str(uuid.uuid4()), "pid": pid, "eid": engineer_emp},
        )


def ensure_sqlite_columns(sync_conn) -> None:
    dialect = sync_conn.dialect.name
    if dialect != "sqlite":
        return
    _patch_table(sync_conn, "projects", PROJECT_COLS)
    _patch_table(sync_conn, "clients", CLIENT_COLS)
    _patch_table(sync_conn, "invoices", INVOICE_COLS)
    _patch_table(sync_conn, "invoice_settings", INVOICE_SETTINGS_COLS)
    _patch_table(sync_conn, "employees", EMPLOYEE_COLS)
    _patch_table(sync_conn, "office_expenses", EXPENSE_COLS)
    _patch_table(sync_conn, "project_assignees", PROJECT_ASSIGNEE_COLS)
    _migrate_assignee_roles(sync_conn)
