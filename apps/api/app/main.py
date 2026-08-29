import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import Base, engine
from app.routers import agent, auth_employees, manager, payments, projects
from app.services.schema_patch import ensure_sqlite_columns

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
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


@app.get("/api/v1/health")
async def health() -> dict:
    return {"ok": True, "app": settings.app_name, "report_version": "phase5-complete"}
