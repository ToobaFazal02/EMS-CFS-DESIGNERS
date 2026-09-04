"""Duration labels for reports — same 8.1 h style as the web Day page."""

from __future__ import annotations


def hours_to_label(hours: float | int | None, places: int = 1) -> str:
    """8.12 hours → '8.1 h'. None → em dash."""
    if hours is None:
        return "—"
    n = float(hours)
    if n < 0:
        n = 0.0
    return f"{n:.{places}f} h"


def hours_to_hm(hours: float | int | None) -> str:
    """Report display hours (alias of hours_to_label)."""
    return hours_to_label(hours)


def hours_to_hms(hours: float | int | None) -> str:
    """Legacy name — reports no longer use clock time (08:58:21)."""
    return hours_to_label(hours)


def minutes_to_hm(minutes: float | int | None) -> str:
    """165 minutes → '2.8 h'."""
    if minutes is None:
        return "—"
    return hours_to_label(float(minutes) / 60.0)


def hours_decimal(hours: float | int | None, places: int = 2) -> float:
    """Numeric decimal for Excel charts only."""
    if hours is None:
        return 0.0
    return round(float(hours), places)
