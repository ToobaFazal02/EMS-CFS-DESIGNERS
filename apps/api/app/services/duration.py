"""Human-readable duration formatting for reports (no confusing decimals)."""

from __future__ import annotations


def hours_to_hm(hours: float | int | None) -> str:
    """2.53 hours → '2h 32m' (not '2.53' which looks like 2:05:03)."""
    if hours is None:
        return "—"
    total_min = int(round(float(hours) * 60))
    if total_min < 0:
        total_min = 0
    h, m = divmod(total_min, 60)
    if h and m:
        return f"{h}h {m:02d}m"
    if h:
        return f"{h}h 00m"
    return f"{m}m"


def hours_to_hms(hours: float | int | None) -> str:
    """2.53 hours → '02:31:48' — same clock style as the old Click Timesheet PDF."""
    if hours is None:
        return "00:00:00"
    total_sec = int(round(float(hours) * 3600))
    if total_sec < 0:
        total_sec = 0
    h, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def minutes_to_hm(minutes: float | int | None) -> str:
    """165.78 minutes → '2h 46m'."""
    if minutes is None:
        return "—"
    return hours_to_hm(float(minutes) / 60.0)


def hours_decimal(hours: float | int | None, places: int = 2) -> float:
    """Keep a numeric decimal for Excel charts only."""
    if hours is None:
        return 0.0
    return round(float(hours), places)
