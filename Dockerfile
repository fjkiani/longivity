FROM python:3.11-slim

WORKDIR /app

# pdfplumber is pure-Python (uses pdfminer.six) — no system deps needed.
# psycopg2-binary bundles its own libpq — no system deps needed.

# Copy pinned requirements first for better layer caching
COPY requirements-pinned.txt requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and install the package itself (no deps, already installed above)
COPY pyproject.toml .
COPY src/ src/
COPY agents/ agents/
RUN pip install --no-cache-dir --no-deps -e .

EXPOSE 8000

CMD ["uvicorn", "longivity.app:app", "--host", "0.0.0.0", "--port", "8000"]
