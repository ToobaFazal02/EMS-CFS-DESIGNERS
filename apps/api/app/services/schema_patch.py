"""SQLite-safe extra columns (create_all does not ALTER existing tables)."""

from sqlalchemy import text


PROJECT_COLS = {
    "contract_value": "FLOAT DEFAULT 0",
    "deposit_pct": "FLOAT DEFAULT 50",
    "currency": "VARCHAR(8) DEFAULT 'USD'",
}


def ensure_sqlite_columns(sync_conn) -> None:
    dialect = sync_conn.dialect.name
    if dialect != "sqlite":
        return
    rows = sync_conn.execute(text("PRAGMA table_info(projects)")).fetchall()
    if not rows:
        return
    existing = {r[1] for r in rows}
    for name, ddl in PROJECT_COLS.items():
        if name not in existing:
            sync_conn.execute(text(f"ALTER TABLE projects ADD COLUMN {name} {ddl}"))
