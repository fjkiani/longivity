"""Async SQLAlchemy engine + session factory."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

_raw_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://longivity:longivity@localhost:5432/longivity",
)

# Render (and many PaaS providers) inject a postgres:// URL.
# SQLAlchemy asyncpg driver requires postgresql+asyncpg://.
DATABASE_URL = _raw_url.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def lifespan_db():
    """Create all tables on startup (idempotent)."""
    from .models import Base as ModelBase  # noqa: F401 — import triggers registration
    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)
    yield
    await engine.dispose()
