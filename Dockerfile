# === Backend Dockerfile ===
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# system deps (for wheels, tz, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# requirements first (better caching)
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# app code
COPY . /app

# entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

# APP_MODULE
ENV APP_MODULE=main:app \
    HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=info

ENTRYPOINT ["/entrypoint.sh"]
