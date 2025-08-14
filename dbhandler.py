# dbhandler.py
from __future__ import annotations
from models import Base, Measurement
import os
from typing import Any, Dict, Optional
from logger import get_logger, setup_logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update

setup_logging()
log = get_logger("dbhandler")


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://drive_user:admin@localhost:8080/drive_test")


def _ensure_asyncpg(dsn: str) -> str:
    log.info("Ensuring asyncpg in DSN: %s", dsn)
    if dsn.startswith("postgresql+asyncpg://"):
        return dsn
    if dsn.startswith("postgresql://"):
        return "postgresql+asyncpg://" + dsn[len("postgresql://"):]
    return dsn


ASYNC_DSN = _ensure_asyncpg(DATABASE_URL)
engine = create_async_engine(ASYNC_DSN, pool_size=10, max_overflow=20)
SessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False)


class PostgresRepository:
    def __init__(self) -> None:
        self._sf = SessionLocal

    async def start(self) -> None:
        log.info("Starting PostgresRepository with DSN: %s", ASYNC_DSN)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def stop(self) -> None:
        log.info("Stopping PostgresRepository")
        await engine.dispose()

    async def insert_measurement_flat(self, payload: Dict[str, Any]) -> None:
        """
        Rozparsuje prichádzajúci measurement JSON na ploché stĺpce a uloží.
        Idempotentne: pri kolízii id sa insert preskočí (DO NOTHING).
        """
        log.info("Inserting measurement")
        m = _extract_fields(payload)
        async with self._sf() as s:
            stmt = insert(Measurement).values(
                **m).on_conflict_do_nothing(index_elements=["id"])
            await s.execute(stmt)
            await s.commit()

    async def apply_rtt(self, meas_id: str, rtt_ms: float) -> None:
        """Doplní RTT iba ak ešte nie je vyplnené (idempotentné)."""
        log.info("Applying RTT for measurement %s: %s ms", meas_id, rtt_ms)
        async with self._sf() as s:
            stmt = (
                update(Measurement)
                .where(Measurement.id == meas_id, Measurement.rtt_ms.is_(None))
                .values(rtt_ms=float(rtt_ms))
            )
            await s.execute(stmt)
            await s.commit()


def _extract_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Bezpečne vytiahne hodnoty z vnoreného JSONu do plochej mapy stĺpcov."""
    log.info("Extracting fields from data")
    radio = data.get("radio") or {}
    pos = data.get("position") or {}
    dev = data.get("device") or {}
    v2x = data.get("v2x") or {}

    return {
        "id": data.get("id"),
        "timestamp_ms": data.get("timestamp_sent"),
        "lat": _f(pos.get("lat")),
        "lon": _f(pos.get("lon")),
        "speed_kmh": _f(pos.get("speed_kmh")),
        "rsrp": _i(radio.get("rsrp")),
        "rsrq": _i(radio.get("rsrq")),
        "sinr": _i(radio.get("sinr")),
        "cell_id": _i(radio.get("cell_id")),
        "network_type": _s(radio.get("network_type")),
        "operator": _s(dev.get("operator")),
        "device_id": _s(dev.get("device_id")),
        "v2x_kind": _s(v2x.get("kind")),
        # rtt_ms sem NEPOSIELAJ – to sa dopĺňa až cez apply_rtt()
    }


def _f(x: Any) -> Optional[float]:
    try:
        return float(x) if x is not None else None
    except Exception:
        return None


def _i(x: Any) -> Optional[int]:
    try:
        return int(x) if x is not None else None
    except Exception:
        return None


def _s(x: Any) -> Optional[str]:
    try:
        return str(x) if x is not None else None
    except Exception:
        return None
