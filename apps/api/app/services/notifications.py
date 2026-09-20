"""Office in-app notifications — create from audit-worthy events."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import OfficeNotification


async def notify_office(
    db: AsyncSession,
    *,
    kind: str,
    title: str,
    body: str = "",
    href: str = "",
    ref_key: str,
    payload: dict | None = None,
) -> OfficeNotification | None:
    """
    Idempotent office alert. Same ref_key → no duplicate.
    Call inside the same transaction as the triggering action; caller commits.
    """
    key = (ref_key or "").strip()[:120]
    if not key:
        return None
    existing = (
        await db.execute(select(OfficeNotification).where(OfficeNotification.ref_key == key))
    ).scalar_one_or_none()
    if existing:
        return existing
    row = OfficeNotification(
        kind=(kind or "info")[:40],
        title=(title or "Alert")[:200],
        body=(body or "")[:2000],
        href=(href or "")[:300],
        ref_key=key,
        payload_json=json.dumps(payload or {}),
        created_at=datetime.utcnow(),
    )
    db.add(row)
    return row
