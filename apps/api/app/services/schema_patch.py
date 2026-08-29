"""SQLite-safe extra columns (create_all does not ALTER existing tables)."""

from sqlalchemy import text


PROJECT_COLS = {
    "contract_value": "FLOAT DEFAULT 0",
    "deposit_pct": "FLOAT DEFAULT 50",
    "currency": "VARCHAR(8) DEFAULT 'USD'",
}

CLIENT_COLS = {
    "phone": "VARCHAR(40) DEFAULT ''",
}

INVOICE_COLS = {
    "bill_to_name": "VARCHAR(120) DEFAULT ''",
    "bill_to_location": "VARCHAR(200) DEFAULT ''",
    "bill_to_phone": "VARCHAR(40) DEFAULT ''",
    "line_items": "TEXT DEFAULT '[]'",
    "invoice_notes": "TEXT DEFAULT ''",
}

INVOICE_SETTINGS_COLS = {
    "header_color": "VARCHAR(20) DEFAULT '#548235'",
    "highlight_color": "VARCHAR(20) DEFAULT '#c9a227'",
}


def _patch_table(sync_conn, table: str, cols: dict[str, str]) -> None:
    rows = sync_conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    if not rows:
        return
    existing = {r[1] for r in rows}
    for name, ddl in cols.items():
        if name not in existing:
            sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def ensure_sqlite_columns(sync_conn) -> None:
    dialect = sync_conn.dialect.name
    if dialect != "sqlite":
        return
    _patch_table(sync_conn, "projects", PROJECT_COLS)
    _patch_table(sync_conn, "clients", CLIENT_COLS)
    _patch_table(sync_conn, "invoices", INVOICE_COLS)
    _patch_table(sync_conn, "invoice_settings", INVOICE_SETTINGS_COLS)
