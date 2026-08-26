"""Classify window titles into Work / Browser / Other (CAD vs chrome)."""

from __future__ import annotations

WORK_KEYWORDS = (
    "framecad",
    "scottsdale",
    "scotsteel",
    "autocad",
    "revit",
    "tekla",
    "solidworks",
    "inventor",
    "rhino",
    "sketchup",
    "bluebeam",
    "pdf-xchange",
    "acrobat",
    "excel",
    "word",
    "teams",  # often work collab — still count as work tools for CFS office
    "outlook",
)

BROWSER_KEYWORDS = (
    "chrome",
    "msedge",
    "edge",
    "firefox",
    "brave",
    "opera",
    "safari",
    "youtube",
    "facebook",
    "instagram",
    "tiktok",
    "whatsapp",
    "netflix",
)


def classify_window(title: str) -> str:
    t = (title or "").lower()
    if not t.strip():
        return "Other"
    for k in WORK_KEYWORDS:
        if k in t:
            return "Work"
    for k in BROWSER_KEYWORDS:
        if k in t:
            return "Browser"
    return "Other"


def summarize_categories(top_windows: list[tuple[str, int]] | None) -> dict[str, int]:
    totals = {"Work": 0, "Browser": 0, "Other": 0}
    for title, qty in top_windows or []:
        cat = classify_window(title)
        totals[cat] = totals.get(cat, 0) + int(qty or 0)
    return totals
