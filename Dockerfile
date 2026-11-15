# Production Dockerfile for Hotel Reservation Service
# Pinned to python:3.13-slim for reproducibility and minimal attack surface
FROM python:3.13-slim

# Enforce immediate unbuffered output and prevent bytecode compilation (.pyc)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install curl for container HEALTHCHECK and clean package caches immediately
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create unprivileged system group and user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -d /app appuser

# Dependency layer (cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code layer
COPY alembic alembic
COPY alembic.ini .
COPY app app
COPY scripts scripts

# Grant ownership to unprivileged user
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Docker-level health check polling the API liveness endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Auto-migrate schema on startup, then launch production ASGI server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
