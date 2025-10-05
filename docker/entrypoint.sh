#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Waiting for DB at ${DATABASE_URL} ..."

RETRIES=30
until python - <<'PY'
import os, asyncio
from sqlalchemy.ext.asyncio import create_async_engine
async def ping():
    dsn = os.getenv("DATABASE_URL")
    eng = create_async_engine(dsn)
    async with eng.begin() as conn:
        await conn.run_sync(lambda *_: None)
    await eng.dispose()
asyncio.run(ping())
PY
do
  RETRIES=$((RETRIES-1))
  if [ "$RETRIES" -le 0 ]; then
    echo "[entrypoint] DB not reachable in time."
    exit 1
  fi
  echo "[entrypoint] DB not ready yet, retrying ..."
  sleep 2
done

echo "[entrypoint] Applying metadata (create_db.py) ..."

# dri drope --recreate

python create_db.py || true

echo "[entrypoint] Starting API (uvicorn ${APP_MODULE}) ..."
exec uvicorn "${APP_MODULE}" --host "${HOST}" --port "${PORT}" --log-level "${LOG_LEVEL}"
