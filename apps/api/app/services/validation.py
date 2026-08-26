"""Shared date/period validation for reports (no future dates)."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import HTTPException

from app.services.timeutil import today_pk


def today_utc() -> date:
    """Deprecated alias — reports use Pakistan calendar day."""
    return today_pk()


def parse_day_or_400(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid date. Use YYYY-MM-DD.") from e


def reject_future_day(day: date) -> None:
    today = today_pk()
    if day > today:
        raise HTTPException(
            status_code=400,
            detail=f"Future dates are not allowed. Today is {today.isoformat()}.",
        )


def reject_future_month(year: int, month: int) -> None:
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be 1–12.")
    if year < 2000 or year > 2100:
        raise HTTPException(status_code=400, detail="Year out of range.")
    today = today_pk()
    if (year, month) > (today.year, today.month):
        raise HTTPException(
            status_code=400,
            detail=f"Future months are not allowed. Current period is {today.year}-{today.month:02d}.",
        )
