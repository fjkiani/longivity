from __future__ import annotations

from fastapi import FastAPI

from .api import router as longevity_router

app = FastAPI(
    title="longivity",
    version="0.1.0",
    description="CrisPRO longevity assessment (RUO)",
)

app.include_router(longevity_router)

