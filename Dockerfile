FROM python:3.11-slim

WORKDIR /app

COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

COPY pyproject.toml .
COPY src/ src/
COPY agents/ agents/
RUN pip install --no-cache-dir --no-deps -e .

EXPOSE 8000

CMD ["uvicorn", "longivity.app:app", "--host", "0.0.0.0", "--port", "8000"]
