"""Daily USD→PKR rates (no hardcoded studio rate).

Source: fawazahmed0 currency-api (jsDelivr + Cloudflare fallback).
Each calendar day is cached under data/fx/usd_pkr_YYYY-MM-DD.json.
"""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path

import httpx

from app.config import get_settings

log = logging.getLogger("ems.fx")

# Last-resort only when CDN is unreachable AND no cached day exists nearby.
EMERGENCY_FALLBACK_USD_PKR = 280.0


def _cache_dir() -> Path:
    p = get_settings().data_path / "fx"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _cache_path(d: date) -> Path:
    return _cache_dir() / f"usd_pkr_{d.isoformat()}.json"


def _read_cache(d: date) -> float | None:
    path = _cache_path(d)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        rate = float(raw.get("usd_pkr") or 0)
        return rate if rate > 0 else None
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _write_cache(d: date, rate: float, source: str) -> None:
    path = _cache_path(d)
    path.write_text(
        json.dumps(
            {"date": d.isoformat(), "usd_pkr": round(float(rate), 4), "source": source},
            indent=0,
        ),
        encoding="utf-8",
    )


def _fetch_remote(d: date) -> float | None:
    """Return PKR per 1 USD for calendar day d, or None."""
    day = d.isoformat()
    urls = [
        f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{day}/v1/currencies/usd.min.json",
        f"https://{day}.currency-api.pages.dev/v1/currencies/usd.min.json",
        f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{day}/v1/currencies/usd.json",
        f"https://{day}.currency-api.pages.dev/v1/currencies/usd.json",
    ]
    if d >= date.today():
        # Future / today: prefer "latest" if dated file missing.
        urls.extend(
            [
                "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.min.json",
                "https://latest.currency-api.pages.dev/v1/currencies/usd.min.json",
            ]
        )
    for url in urls:
        try:
            with httpx.Client(timeout=8.0, follow_redirects=True) as client:
                r = client.get(url)
            if r.status_code != 200:
                continue
            data = r.json()
            block = data.get("usd") if isinstance(data, dict) else None
            if not isinstance(block, dict):
                continue
            pkr = block.get("pkr")
            if pkr is None:
                continue
            rate = float(pkr)
            if rate > 0:
                return rate
        except Exception as exc:  # noqa: BLE001 — network/parse; try next URL
            log.debug("FX fetch fail %s: %s", url, exc)
            continue
    return None


def usd_pkr_rate_for(d: date | None) -> tuple[float, str, str]:
    """Return (rate, rate_date_iso, note). Walks back up to 10 days for weekends/holidays."""
    if d is None:
        d = date.today()
    # Don't ask CDN for far-future dates.
    if d > date.today():
        d = date.today()

    for back in range(0, 11):
        day = d - timedelta(days=back)
        cached = _read_cache(day)
        if cached is not None:
            note = "cache" if back == 0 else f"cache nearest -{back}d"
            return cached, day.isoformat(), note
        fetched = _fetch_remote(day)
        if fetched is not None:
            _write_cache(day, fetched, "currency-api")
            note = "live" if back == 0 else f"live nearest -{back}d"
            return fetched, day.isoformat(), note

    # Emergency: only reuse a cached day within 14 days of the request.
    files = sorted(_cache_dir().glob("usd_pkr_*.json"), reverse=True)
    for path in files[:60]:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            rate = float(raw.get("usd_pkr") or 0)
            cached_day = date.fromisoformat(str(raw.get("date") or path.stem[-10:]))
            if rate > 0 and abs((cached_day - d).days) <= 14:
                return rate, cached_day.isoformat(), "nearby cache"
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            continue

    log.warning("FX unavailable for %s — using emergency fallback %.2f", d, EMERGENCY_FALLBACK_USD_PKR)
    return EMERGENCY_FALLBACK_USD_PKR, d.isoformat(), "emergency fallback"


def usd_to_pkr(amount_usd: float, d: date | None) -> tuple[float, float, str]:
    rate, rate_day, _ = usd_pkr_rate_for(d)
    return round(float(amount_usd or 0) * rate, 2), rate, rate_day


def pkr_to_usd(amount_pkr: float, d: date | None) -> tuple[float, float, str]:
    rate, rate_day, _ = usd_pkr_rate_for(d)
    if rate <= 0:
        rate = EMERGENCY_FALLBACK_USD_PKR
    return round(float(amount_pkr or 0) / rate, 2), rate, rate_day
