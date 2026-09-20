import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_device_from_token
from app.config import get_settings
from app.db import get_db
from app.live import live_hub
from app.models import ActivityBucket, Device, Punch, PunchType, Screenshot, WindowSample
from app.schemas import ActivityIn, PunchIn, PunchOut

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])
settings = get_settings()

# ── App version endpoints (no auth — Agent / Manager check on startup) ────
# Bump these whenever you ship a new Agent zip or Manager Setup.exe.
LATEST_AGENT_VERSION = "1.1.6"
LATEST_MANAGER_VERSION = "0.1.6"
DOWNLOADS_PAGE = "https://ems.cfsdesigners.com/downloads"
AGENT_PACKAGE_URL = f"{DOWNLOADS_PAGE}/CFS-Agent-Install.zip"
MANAGER_SETUP_URL = f"{DOWNLOADS_PAGE}/CFS-Designers-Manager-Setup.exe"


@router.get("/version", tags=["agent"])
async def agent_version() -> dict:
    """
    Latest Agent + Manager versions and download URLs.
    Agents and the Manager desktop app call this to show "Update available"
    and (from 1.1.2 / 0.1.2) to run click → background install.
    No authentication required. Does not touch SQLite / employee data.
    """
    return {
        "agent_version": LATEST_AGENT_VERSION,
        "download_url": DOWNLOADS_PAGE,
        "agent_package_url": AGENT_PACKAGE_URL,
        "manager_version": LATEST_MANAGER_VERSION,
        "manager_download_url": MANAGER_SETUP_URL,
    }


def _bucket_floor(dt: datetime) -> datetime:
    minute = (dt.minute // 30) * 30
    return dt.replace(minute=minute, second=0, microsecond=0)


@router.post("/punches", response_model=PunchOut)
async def upsert_punch(
    body: PunchIn,
    device: Annotated[Device, Depends(get_device_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PunchOut:
    existing = await db.get(Punch, body.id)
    if existing:
        return PunchOut(
            id=existing.id,
            type=existing.type,
            server_at=existing.server_at,
            session_id=existing.session_id,
            employee_id=existing.employee_id,
        )

    # Determine open session
    result = await db.execute(
        select(Punch)
        .where(Punch.employee_id == device.employee_id)
        .order_by(Punch.server_at.desc())
        .limit(20)
    )
    recent = list(result.scalars().all())
    open_session = None
    for p in recent:
        if p.type == PunchType.sign_out:
            break
        if p.type == PunchType.sign_in:
            open_session = p.session_id
            break

    if body.type == PunchType.sign_in:
        session_id = body.session_id or str(uuid.uuid4())
        if open_session:
            raise HTTPException(
                status_code=400,
                detail="Already signed in on the server. Tap Sign Out first, then Sign In again.",
            )
    else:
        session_id = body.session_id or open_session
        if not session_id:
            raise HTTPException(
                status_code=400,
                detail="No open session. Tap Sign In first.",
            )
        if body.type == PunchType.sign_out and not open_session:
            raise HTTPException(status_code=400, detail="Already signed out.")

    punch = Punch(
        id=body.id,
        employee_id=device.employee_id,
        type=body.type,
        server_at=datetime.utcnow(),
        client_sent_at=body.client_sent_at,
        session_id=session_id,
        source="agent",
    )
    db.add(punch)

    if body.type == PunchType.sign_in:
        device.live_status = "working"
    elif body.type == PunchType.break_in:
        device.live_status = "break"
    elif body.type == PunchType.break_out:
        device.live_status = "working"
    elif body.type == PunchType.sign_out:
        device.live_status = "offline"
        device.last_window = ""

    device.last_seen_at = datetime.utcnow()
    await db.commit()
    await db.refresh(punch)

    from app.models import Employee

    emp = await db.get(Employee, device.employee_id)
    await live_hub.publish(
        {
            "type": "punch",
            "employee_id": device.employee_id,
            "code": emp.code if emp else "",
            "full_name": emp.full_name if emp else "",
            "status": device.live_status,
            "punch_type": punch.type.value,
        }
    )
    return PunchOut(
        id=punch.id,
        type=punch.type,
        server_at=punch.server_at,
        session_id=punch.session_id,
        employee_id=punch.employee_id,
    )


@router.get("/session")
async def agent_session(
    device: Annotated[Device, Depends(get_device_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Tell agent if server still has an open Sign In (fixes stuck local OFF / server ON)."""
    result = await db.execute(
        select(Punch)
        .where(Punch.employee_id == device.employee_id)
        .order_by(Punch.server_at.desc())
        .limit(20)
    )
    recent = list(result.scalars().all())
    open_session = None
    for p in recent:
        if p.type == PunchType.sign_out:
            break
        if p.type == PunchType.sign_in:
            open_session = p.session_id
            break
    return {
        "signed_in": bool(open_session),
        "session_id": open_session,
        "live_status": device.live_status,
    }


@router.post("/activity")
async def post_activity(
    body: ActivityIn,
    device: Annotated[Device, Depends(get_device_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    # Require an open Sign In — prevents click dumps with empty Sessions on the daily PDF
    recent = list(
        (
            await db.execute(
                select(Punch)
                .where(Punch.employee_id == device.employee_id)
                .order_by(Punch.server_at.desc())
                .limit(20)
            )
        ).scalars().all()
    )
    open_session = None
    for p in recent:
        if p.type == PunchType.sign_out:
            break
        if p.type == PunchType.sign_in:
            open_session = p.session_id
            break
    if not open_session:
        raise HTTPException(
            status_code=409,
            detail="Not signed in. Tap Sign In before activity is recorded.",
        )

    now = datetime.utcnow()
    bucket_start = _bucket_floor(now)
    result = await db.execute(
        select(ActivityBucket).where(
            ActivityBucket.employee_id == device.employee_id,
            ActivityBucket.bucket_start == bucket_start,
        )
    )
    bucket = result.scalar_one_or_none()
    if not bucket:
        bucket = ActivityBucket(
            employee_id=device.employee_id,
            bucket_start=bucket_start,
            mouse_clicks=0,
            key_presses=0,
            idle_seconds=0,
        )
        db.add(bucket)
    bucket.mouse_clicks += max(body.mouse_clicks, 0)
    bucket.key_presses += max(body.key_presses, 0)
    bucket.idle_seconds += max(body.idle_seconds, 0)

    if body.window_title:
        db.add(
            WindowSample(
                employee_id=device.employee_id,
                sampled_at=now,
                title=body.window_title[:500],
                clicks=max(body.mouse_clicks, 0),
            )
        )
        device.last_window = body.window_title[:500]

    status = body.status if body.status in ("working", "break", "idle") else "working"
    if device.live_status != "offline":
        device.live_status = status
    device.last_clicks_delta = body.mouse_clicks
    device.last_keys_delta = body.key_presses
    device.idle_seconds = body.idle_seconds
    device.last_seen_at = now
    await db.commit()

    from app.models import Employee

    emp = await db.get(Employee, device.employee_id)
    thumb = None
    if device.last_screenshot_id:
        thumb = f"/api/v1/screenshots/{device.last_screenshot_id}/file"
    await live_hub.publish(
        {
            "type": "activity",
            "employee_id": device.employee_id,
            "code": emp.code if emp else "",
            "full_name": emp.full_name if emp else "",
            "status": device.live_status,
            "last_window": device.last_window,
            "last_clicks_delta": device.last_clicks_delta,
            "last_keys_delta": device.last_keys_delta,
            "idle_seconds": device.idle_seconds,
            "last_screenshot_url": thumb,
            "last_seen_at": now.isoformat(),
        }
    )
    return {"ok": True}


@router.post("/screenshots")
async def upload_screenshot(
    device: Annotated[Device, Depends(get_device_from_token)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
    captured_at: str | None = Form(None),
) -> dict:
    if file.content_type not in ("image/jpeg", "image/jpg", "image/png", "image/webp"):
        raise HTTPException(status_code=400, detail="Only JPEG/PNG/WebP allowed")
    raw = await file.read()
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")

    shot_id = str(uuid.uuid4())
    now = datetime.utcnow()
    rel = Path("screenshots") / device.employee_id / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d")
    abs_dir = settings.data_path / rel
    abs_dir.mkdir(parents=True, exist_ok=True)
    dest = abs_dir / f"{shot_id}.jpg"

    # Normalize to JPEG
    from io import BytesIO

    try:
        probe = Image.open(BytesIO(raw))
        probe.verify()
        img = Image.open(BytesIO(raw))
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((1600, 900))
        img.save(dest, "JPEG", quality=72, optimize=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image file") from exc

    shot = Screenshot(
        id=shot_id,
        employee_id=device.employee_id,
        captured_at=now,
        path=str(rel / f"{shot_id}.jpg").replace("\\", "/"),
        bytes=dest.stat().st_size,
        content_type="image/jpeg",
    )
    db.add(shot)
    device.last_screenshot_id = shot_id
    device.last_seen_at = now
    await db.commit()

    from app.models import Employee

    emp = await db.get(Employee, device.employee_id)
    await live_hub.publish(
        {
            "type": "screenshot",
            "employee_id": device.employee_id,
            "code": emp.code if emp else "",
            "full_name": emp.full_name if emp else "",
            "status": device.live_status,
            "last_screenshot_url": f"/api/v1/screenshots/{shot_id}/file",
            "last_seen_at": now.isoformat(),
        }
    )
    return {"id": shot_id, "url": f"/api/v1/screenshots/{shot_id}/file"}
