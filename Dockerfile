FROM python:3.11-slim

WORKDIR /app

# pdfplumber is pure-Python (uses pdfminer.six) — no system deps needed.
# psycopg2-binary bundles its own libpq — no system deps needed.

# Python deps — install core deps first for better layer caching,
# then the full package via -e .
COPY pyproject.toml .
COPY src/ src/
COPY agents/ agents/

RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    pydantic>=2.0.0 \
    sqlalchemy[asyncio]>=2.0.0 \
    asyncpg \
    alembic \
    python-jose[cryptography] \
    passlib[bcrypt] \
    pdfplumber \
    python-multipart \
    aiofiles \
    psycopg2-binary \
    httpx>=0.27.0 \
    && pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "longivity.app:app", "--host", "0.0.0.0", "--port", "8000"]
