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
    version="0.3.0",
    description=(
        "End-to-end longevity clinic platform. "
        "Patient management, biomarker tracking, PDF lab import, "
        "PhenoAge assessment, MR-validated compound recommendations, "
        "and N-of-1 trial protocols. (RUO)"
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

# New patient platform endpoints
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(panels_router)
app.include_router(upload_router)
app.include_router(assessment_router)


@app.get("/", tags=["root"])
async def root():
    return {
        "service": "Longivity Patient Platform",
        "version": "0.3.0",
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
            "science": [
                "/api/v1/longevity/assessment_level0",
                "/api/v1/longevity/full_assessment",
                "/api/v1/longevity/cardiovascular_risk",
                "/api/v1/longevity/nof1/protocol",
                "/api/v1/longevity/agent/assess",
            ],
        },
    }
