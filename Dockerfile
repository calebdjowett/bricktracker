FROM python:3.11-slim

WORKDIR /app/backend

COPY backend/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir .

COPY backend/ ./
COPY database/ /app/database/

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]