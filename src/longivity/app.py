
# ── Production CORS lockdown ──────────────────────────────────────────────────
import os as _os
_env = _os.getenv("ENV", "development")
_origins = _os.getenv("ALLOWED_ORIGINS", "")
if _env == "production" and "*" in _origins:
    raise RuntimeError(
        "CORS wildcard '*' is not allowed in production. "
        "Set ALLOWED_ORIGINS to specific origins in your environment."
    )

"""Longivity FastAPI application — full patient platform."""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from .api import router as longevity_router
from .routers.auth import router as auth_router
from .routers.patients import router as patients_router
from .routers.panels import router as panels_router
from .routers.upload import router as upload_router
from .routers.assessment import router as assessment_router
from .routers.test_orders import router as test_orders_router
from .routers.timeline import router as timeline_router
from .routers.intelligence import router as intelligence_router
from .routers.demo import router as demo_router
from .routers.evidence import router as evidence_router
from .routers.nutrition import router as nutrition_router
from .research_intelligence.router import router as ri_router
from .routers.benchmark import router as benchmark_router

# ── Structured logging ────────────────────────────────────────────────────────
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)
_slog = structlog.get_logger("longivity.app")

# ── Rate limiting ─────────────────────────────────────────────────────────────
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

_RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")
limiter = Limiter(key_func=get_remote_address, default_limits=[_RATE_LIMIT_DEFAULT])

logger = logging.getLogger("longivity.keepalive")

# ── Keep-alive ────────────────────────────────────────────────────────────────
# Render free tier spins down after 15 min idle. This background task pings
# the backend's own healthz endpoint every 10 minutes to prevent cold starts.
# Uses only stdlib (urllib) — no extra dependencies.
_KEEPALIVE_URL = os.getenv(
    "KEEPALIVE_URL",
    "https://longivity-backend.onrender.com/api/v1/longevity/healthz",
)
_KEEPALIVE_INTERVAL = int(os.getenv("KEEPALIVE_INTERVAL_SECONDS", "600"))  # 10 min


async def _keepalive_loop() -> None:
    """Ping own healthz endpoint every KEEPALIVE_INTERVAL_SECONDS."""
    import urllib.request  # stdlib — always available

    await asyncio.sleep(30)  # wait for startup to settle
    while True:
        try:
            with urllib.request.urlopen(_KEEPALIVE_URL, timeout=20) as resp:
                body = resp.read(100).decode("utf-8", errors="replace")
                logger.info("keep-alive ping → %s %s", resp.status, body)
        except Exception as exc:
            logger.warning("keep-alive ping failed: %s", exc)
        await asyncio.sleep(_KEEPALIVE_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup, then start keep-alive background task."""
    # Start keep-alive pinger only in production (RENDER env var set by Render platform)
    task: asyncio.Task | None = None
    if os.getenv("RENDER") or os.getenv("KEEPALIVE_URL"):
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
    version="0.5.0",
    description=(
        "End-to-end longevity clinic platform with research intelligence. "
        "Patient management, biomarker tracking, PDF lab import, "
        "PhenoAge assessment, MR-validated compound recommendations, "
        "N-of-1 trial protocols, and agent-driven test ordering. (RUO)"
    ),
    lifespan=lifespan,
)

# Wire rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
_slog.info("rate_limiter_configured", default_limit=_RATE_LIMIT_DEFAULT)

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
app.include_router(demo_router)
app.include_router(evidence_router)
app.include_router(nutrition_router)
app.include_router(ri_router)
app.include_router(benchmark_router)


@app.get("/", tags=["root"])
async def root():
    return {
        "service": "Longivity Patient Platform",
        "version": "0.5.0",
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
            "demo": [
                "GET  /api/v1/demo/status",
                "POST /api/v1/demo/reset",
            ],
            "evidence": [
                "GET /api/v1/patients/{id}/evidence/compound/{compound_id}",
                "GET /api/v1/patients/{id}/evidence/hallmark/{hallmark}",
                "GET /api/v1/patients/{id}/evidence/cancer-risk",
                "POST /api/v1/research-intelligence/research",
            ],
            "intelligence": [
                "GET /api/v1/patients/{id}/intelligence",
                "GET /api/v1/clinic/intelligence",
            ],
            "benchmark": [
                "GET /api/v1/longevity/benchmark/cohorts",
                "GET /api/v1/longevity/benchmark/evals",
                "GET /api/v1/longevity/benchmark/trust",
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
