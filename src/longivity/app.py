"""Longivity FastAPI application — full patient platform."""
from __future__ import annotations

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup."""
    try:
        from .db.database import lifespan_db
        async with lifespan_db():
            yield
    except Exception as e:
        # If DB is not available (e.g. no postgres in dev), log and continue
        import logging
        logging.warning(f"DB startup warning (non-fatal in no-DB mode): {e}")
        yield


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "https://*.railway.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
# Existing science endpoints (unchanged)
app.include_router(longevity_router)

# Patient platform endpoints
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(panels_router)
app.include_router(upload_router)
app.include_router(assessment_router)

# Test ordering agent endpoints (new)
app.include_router(test_orders_router)

# Timeline endpoint (Phase 7A)
app.include_router(timeline_router)


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
            "science": [
                "/api/v1/longevity/assessment_level0",
                "/api/v1/longevity/full_assessment",
                "/api/v1/longevity/cardiovascular_risk",
                "/api/v1/longevity/nof1/protocol",
                "/api/v1/longevity/agent/assess",
            ],
        },
    }
