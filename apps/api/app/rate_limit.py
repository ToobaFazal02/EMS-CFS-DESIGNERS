"""In-memory IP rate limits for public auth endpoints (single-process uvicorn)."""

from collections import defaultdict
from time import monotonic

from fastapi import HTTPException, Request, status

_hits: dict[str, list[float]] = defaultdict(list)


def client_ip(request: Request) -> str:
    peer = request.client.host if request.client else ""
    if peer in ("127.0.0.1", "::1"):
        forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
        if forwarded:
            return forwarded[:64]
    return peer or "unknown"


def hit(key: str, limit: int = 20, window_seconds: float = 300) -> None:
    now = monotonic()
    bucket = [t for t in _hits[key] if now - t < window_seconds]
    if len(bucket) >= limit:
        _hits[key] = bucket
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Wait a minute and try again.",
        )
    bucket.append(now)
    _hits[key] = bucket
    if len(_hits) > 4000:
        stale = [k for k, ts in _hits.items() if not ts or now - ts[-1] > window_seconds]
        for k in stale[:800]:
            _hits.pop(k, None)
