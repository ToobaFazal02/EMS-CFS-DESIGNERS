"""Phase C project helpers — codes, scopes, assignees."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import WorkScope

PKT = ZoneInfo("Asia/Karachi")

SCOPE_VALUES = {s.value for s in WorkScope}
SCOPE_LABELS = {
    WorkScope.estimation.value: "Estimation",
    WorkScope.detailing.value: "Detailing",
    WorkScope.detailing_engineering.value: "Detailing + Engineering",
}


def normalize_initial(raw: str | None, fallback_name: str = "") -> str:
    s = "".join(ch for ch in (raw or "").strip().upper() if ch.isalnum())
    if s:
        return s[:4]
    letters = "".join(ch for ch in (fallback_name or "").upper() if ch.isalpha())
    return (letters[:1] or "X")


def pkt_ddmmyy(when: datetime | None = None) -> str:
    d = when.astimezone(PKT) if when and when.tzinfo else (when or datetime.now(PKT))
    if d.tzinfo is None:
        d = d.replace(tzinfo=PKT)
    return d.astimezone(PKT).strftime("%d%m%y")


def build_project_code(initial: str, when: datetime | None = None, override: str = "") -> str:
    ov = "".join(ch for ch in (override or "").strip().upper() if ch.isalnum() or ch in "-_")
    if ov:
        return ov[:32]
    ini = normalize_initial(initial) or "X"
    return f"{ini}{pkt_ddmmyy(when)}"[:32]


def normalize_scope(raw: str | None) -> str:
    s = (raw or "").strip().lower().replace(" ", "_").replace("+", "_").replace("-", "_")
    while "__" in s:
        s = s.replace("__", "_")
    s = s.strip("_")
    aliases = {
        "estimation": WorkScope.estimation.value,
        "detailing": WorkScope.detailing.value,
        "detailing_engineering": WorkScope.detailing_engineering.value,
        "detailingengineering": WorkScope.detailing_engineering.value,
        "detailing_and_engineering": WorkScope.detailing_engineering.value,
    }
    return aliases.get(s, "")


def resolve_assignee_ids(assignee_id: str | None, assignee_ids: list[str] | None) -> list[str]:
    ids: list[str] = []
    for x in assignee_ids or []:
        v = (x or "").strip()
        if v and v not in ids:
            ids.append(v)
    lead = (assignee_id or "").strip()
    if lead and lead not in ids:
        ids.insert(0, lead)
    elif lead and lead in ids:
        ids = [lead] + [i for i in ids if i != lead]
    return ids
