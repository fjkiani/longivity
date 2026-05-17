"""Longivity FastAPI application — full patient platform."""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as longevity_router
from .routers.auth import router as auth_router
from .routers.patients import router as patients_router
from .routers.panels import router as panels_router
from .routers.upload import router as upload_router
from .routers.assessment import router as assessment_router
from .routers.test_orders import router as test_orders_router
from .routers.timeline import router as timeline_router
from .routers.intelligence import router as intelligence_router

logger = logging.getLogger("longivity.keepalive")

# ── Keep-alive ────────────────────────────────────────────────────────────────
# Render free tier spins down after 15 min idle. This background task pings
# the backend's own healthz endpoint every 10 minutes to prevent cold starts.
_KEEPALIVE_URL = os.getenv(
    "KEEPALIVE_URL",
    "https://longivity-backend.onrender.com/api/v1/longevity/healthz",
)
_KEEPALIVE_INTERVAL = int(os.getenv("KEEPALIVE_INTERVAL_SECONDS", "600"))  # 10 min


async def _keepalive_loop() -> None:
    """Ping own healthz endpoint every KEEPALIVE_INTERVAL_SECONDS."""
    # Lazy import — httpx may not be installed in all environments
    try:
        import httpx  # noqa: PLC0415
    except ImportError:
        logger.warning("httpx not installed — keep-alive disabled")
        return

    await asyncio.sleep(30)  # wait for startup to settle
    async with httpx.AsyncClient(timeout=20) as client:
        while True:
            try:
                r = await client.get(_KEEPALIVE_URL)
                logger.info("keep-alive ping → %s %s", r.status_code, r.text[:60])
            except Exception as exc:
                logger.warning("keep-alive ping failed: %s", exc)
            await asyncio.sleep(_KEEPALIVE_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup, then start keep-alive background task."""
    # Start keep-alive pinger (only in production — activated by RENDER or KEEPALIVE_URL env var)
    task: asyncio.Task | None = None
    if os.getenv("KEEPALIVE_URL") or os.getenv("RENDER"):
        task = asyncio.create_task(_keepalive_loop())
        logger.info(
            "keep-alive task started (interval=%ds, url=%s)",
            _KEEPALIVE_INTERVAL,
            _KEEPALIVE_URL,
        )

    try:
        from .db.database import lifespan_db
        async with lifespan_db():
            yield
    except Exception as e:
        logging.warning(f"DB startup warning (non-fatal in no-DB mode): {e}")
        yield
    finally:
        if task:
            task.cancel()


app = FastAPI(
    title="Longivity — Longevity Patient Platform",
    version="0.4.0",
    description=(
        "End-to-end longevity clinic platform. "
        "Patient management, biomarker tracking, PDF lab import, "
        "PhenoAge assessment, MR-validated compound recommendations, "
        "N-of-1 trial protocols, and agent-driven test ordering. (RUO)"
    ),
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Read comma-separated origins from env var; fall back to localhost for dev.
_origins_env = os.getenv("ALLOWED_ORIGINS", "")
_origins: list[str] = (
    [o.strip() for o in _origins_env.split(",") if o.strip()]
    if _origins_env
    else [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(longevity_router)
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(panels_router)
app.include_router(upload_router)
app.include_router(assessment_router)
app.include_router(test_orders_router)
app.include_router(timeline_router)
app.include_router(intelligence_router)


@app.get("/", tags=["root"])
async def root():
    return {
        "service": "Longivity Patient Platform",
        "version": "0.4.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "auth": ["/api/v1/auth/register", "/api/v1/auth/login", "/api/v1/auth/me"],
            "patients": ["/api/v1/patients", "/api/v1/patients/{id}"],
            "panels": ["/api/v1/patients/{id}/panels"],
            "upload": ["/api/v1/patients/{id}/upload"],
            "assessment": [
                "/api/v1/patients/{id}/assessment",
                "/api/v1/patients/{id}/longitudinal",
                "/api/v1/patients/{id}/nof1/{compound_id}",
            ],
            "test_ordering": [
                "GET  /api/v1/patients/{id}/test-order",
                "POST /api/v1/patients/{id}/test-order",
                "GET  /api/v1/patients/{id}/test-order/{order_id}",
                "GET  /api/v1/patients/{id}/test-order/{order_id}/requisition",
                "GET  /api/v1/patients/{id}/test-orders",
                "GET  /api/v1/patients/{id}/biomarker-gaps",
                "GET  /api/v1/markers",
                "GET  /api/v1/markers/{marker_key}",
                "GET  /api/v1/panels",
                "GET  /api/v1/panels/{panel_id}",
                "GET  /api/v1/registry/metadata",
            ],
            "timeline": ["/api/v1/patients/{id}/timeline"],
            "intelligence": [
                "GET /api/v1/patients/{id}/intelligence",
                "GET /api/v1/clinic/intelligence",
            ],
            "science": [
                "/api/v1/longevity/assessment_level0",
                "/api/v1/longevity/full_assessment",
                "/api/v1/longevity/cardiovascular_risk",
                "/api/v1/longevity/nof1/protocol",
                "/api/v1/longevity/agent/assess",
            ],
        },
    }
