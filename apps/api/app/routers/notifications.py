"""Office notification bell API — list / unread / mark read (admin · manager · HR)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, is_office, is_office_or_demo
from app.db import get_db
from app.models import Employee, OfficeNotification, OfficeNotificationRead

router = APIRouter(prefix="/api/v1", tags=["notifications"])


class NotificationOut(BaseModel):
    id: str
    kind: str
    title: str
    body: str
    href: str
    created_at: str
    read: bool


class UnreadOut(BaseModel):
    unread: int = Field(ge=0)


class MarkReadIn(BaseModel):
    ids: list[str] = Field(default_factory=list)


def _require_office(user: Employee) -> None:
    if not (is_office(user) or is_office_or_demo(user)):
        raise HTTPException(status_code=403, detail="Office notifications are for Admin / Manager / HR.")


def _iso(dt: datetime | None) -> str:
    if not dt:
        return ""
    return dt.isoformat() + ("Z" if dt.tzinfo is None else "")


@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(
    user: Annotated[Employee, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(40, ge=1, le=100),
    unread_only: bool = Query(False),
) -> list[NotificationOut]:
    _require_office(user)
    rows = (
        await db.execute(
            select(OfficeNotification).order_by(OfficeNotification.created_at.desc()).limit(limit)
        )
    ).scalars().all()
    if not rows:
        return []
    ids = [r.id for r in rows]
    read_ids = set(
        (
            await db.execute(
                select(OfficeNotificationRead.notification_id).where(
                    OfficeNotificationRead.employee_id == user.id,
                    OfficeNotificationRead.notification_id.in_(ids),
                )
            )
        )
        .scalars()
        .all()
    )
    out: list[NotificationOut] = []
    for r in rows:
        is_read = r.id in read_ids
        if unread_only and is_read:
            continue
        out.append(
            NotificationOut(
                id=r.id,
                kind=r.kind,
                title=r.title,
                body=r.body or "",
                href=r.href or "",
                created_at=_iso(r.created_at),
                read=is_read,
            )
        )
    return out


@router.get("/notifications/unread-count", response_model=UnreadOut)
async def unread_count(
    user: Annotated[Employee, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UnreadOut:
    _require_office(user)
    total = (
        await db.execute(select(func.count()).select_from(OfficeNotification))
    ).scalar() or 0
    read_n = (
        await db.execute(
            select(func.count())
            .select_from(OfficeNotificationRead)
            .where(OfficeNotificationRead.employee_id == user.id)
        )
    ).scalar() or 0
    return UnreadOut(unread=max(0, int(total) - int(read_n)))


@router.post("/notifications/mark-read")
async def mark_read(
    body: MarkReadIn,
    user: Annotated[Employee, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    _require_office(user)
    ids = [i for i in (body.ids or []) if i][:100]
    if not ids:
        return {"ok": True, "marked": 0}
    existing = set(
        (
            await db.execute(select(OfficeNotification.id).where(OfficeNotification.id.in_(ids)))
        )
        .scalars()
        .all()
    )
    already = set(
        (
            await db.execute(
                select(OfficeNotificationRead.notification_id).where(
                    OfficeNotificationRead.employee_id == user.id,
                    OfficeNotificationRead.notification_id.in_(list(existing)),
                )
            )
        )
        .scalars()
        .all()
    )
    marked = 0
    now = datetime.utcnow()
    for nid in existing:
        if nid in already:
            continue
        db.add(
            OfficeNotificationRead(
                notification_id=nid,
                employee_id=user.id,
                read_at=now,
            )
        )
        marked += 1
    await db.commit()
    return {"ok": True, "marked": marked}


@router.post("/notifications/mark-all-read")
async def mark_all_read(
    user: Annotated[Employee, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    _require_office(user)
    all_ids = set((await db.execute(select(OfficeNotification.id))).scalars().all())
    already = set(
        (
            await db.execute(
                select(OfficeNotificationRead.notification_id).where(
                    OfficeNotificationRead.employee_id == user.id
                )
            )
        )
        .scalars()
        .all()
    )
    now = datetime.utcnow()
    marked = 0
    for nid in all_ids - already:
        db.add(
            OfficeNotificationRead(
                notification_id=nid,
                employee_id=user.id,
                read_at=now,
            )
        )
        marked += 1
    await db.commit()
    return {"ok": True, "marked": marked}
