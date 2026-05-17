FROM python:3.11-slim

WORKDIR /app

# System deps for pdfplumber
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpoppler-cpp-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml .
COPY src/ src/
COPY agents/ agents/

RUN pip install --no-cache-dir \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    pydantic>=2.0.0 \
    langgraph>=0.2.0 \
    langchain-core>=0.3.0 \
    sqlalchemy[asyncio]>=2.0.0 \
    asyncpg \
    alembic \
    python-jose[cryptography] \
    passlib[bcrypt] \
    pdfplumber \
    python-multipart \
    aiofiles \
    psycopg2-binary \
    httpx \
    && pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "longivity.app:app", "--host", "0.0.0.0", "--port", "8000"]
