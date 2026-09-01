"""Asia/Karachi (PKT, UTC+5) helpers for reports & display."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo

    try:
        PK = ZoneInfo("Asia/Karachi")
    except Exception:
        PK = timezone(timedelta(hours=5), name="PKT")
except Exception:
    PK = timezone(timedelta(hours=5), name="PKT")


def now_pk() -> datetime:
    return datetime.now(PK)


def today_pk() -> date:
    return now_pk().date()


def monday_of(d: date) -> date:
    """ISO week start (Monday) for a PKT calendar date."""
    return d - timedelta(days=d.weekday())


def to_pk(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PK)


def format_generated() -> str:
    return now_pk().strftime("%d-%b-%Y %H:%M")


def format_pk_time(dt: datetime | None, with_seconds: bool = True) -> str:
    local = to_pk(dt)
    if not local:
        return "—"
    fmt = "%H:%M:%S" if with_seconds else "%H:%M"
    return local.strftime(fmt)


def format_pk_datetime(dt: datetime | None) -> str:
    local = to_pk(dt)
    if not local:
        return "—"
    return local.strftime("%d-%b-%Y %I:%M:%S %p")
