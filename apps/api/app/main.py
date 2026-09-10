import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import get_settings
from app.db import Base, engine
from app.routers import agent, auth_employees, expenses, manager, partner_shares, payments, projects
from app.services.schema_patch import ensure_sqlite_columns

settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response


def _assert_safe_to_serve() -> None:
    if settings.secret_is_weak():
        raise RuntimeError(
            "SECRET_KEY is missing or too weak. Generate one with: "
            'python -c "import secrets; print(secrets.token_hex(32))" '
            "and put it in apps/api/.env"
        )
    if settings.is_production and settings.auto_seed_samples:
        raise RuntimeError("AUTO_SEED_SAMPLES must be false when EMS_ENV=production")


@asynccontextmanager
async def lifespan(_: FastAPI):
    _assert_safe_to_serve()
    settings.data_path  # ensure dirs
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(ensure_sqlite_columns)
    if settings.auto_seed_samples:
        try:
            from app.seed import ensure_samples

            await ensure_samples()
        except Exception as exc:  # noqa: BLE001 — startup must not crash
            print("Sample seed skipped:", exc)
    from app.services.retention import retention_loop

    retain_task = asyncio.create_task(retention_loop())
    yield
    retain_task.cancel()
    try:
        await retain_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_employees.router)
app.include_router(agent.router)
app.include_router(manager.router)
app.include_router(projects.router)
app.include_router(payments.router)
app.include_router(expenses.router)
app.include_router(partner_shares.router)


@app.get("/api/v1/health")
async def health() -> dict:
    return {"ok": True, "app": settings.app_name, "report_version": "phase5-complete"}
