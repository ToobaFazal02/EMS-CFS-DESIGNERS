"""Delete screenshot files + DB rows older than SCREENSHOT_RETENTION_DAYS."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import Device, Screenshot

log = logging.getLogger("ems.retention")


async def purge_expired_screenshots() -> int:
    settings = get_settings()
    days = max(1, int(settings.screenshot_retention_days or 60))
    cutoff = datetime.utcnow() - timedelta(days=days)
    async with SessionLocal() as db:
        result = await db.execute(select(Screenshot).where(Screenshot.captured_at < cutoff))
        rows = list(result.scalars().all())
        if not rows:
            return 0
        ids = {row.id for row in rows}
        devices = await db.execute(select(Device).where(Device.last_screenshot_id.in_(ids)))
        for device in devices.scalars():
            device.last_screenshot_id = None
        deleted = 0
        for shot in rows:
            path = settings.data_path / shot.path
            try:
                if path.is_file():
                    path.unlink()
            except OSError as exc:
                log.warning("Could not delete screenshot file %s: %s", path, exc)
            await db.delete(shot)
            deleted += 1
        await db.commit()
        return deleted


async def retention_loop() -> None:
    await asyncio.sleep(15)
    while True:
        try:
            n = await purge_expired_screenshots()
            days = get_settings().screenshot_retention_days
            if n:
                log.info("Purged %s screenshots older than %s days", n, days)
        except Exception:
            log.exception("Screenshot retention purge failed")
        await asyncio.sleep(24 * 60 * 60)
