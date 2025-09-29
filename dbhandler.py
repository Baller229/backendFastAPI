# dbhandler.py
from __future__ import annotations
from models import Base, Measurement, SessionStats
import os
from typing import Any, Dict, Optional
from logger import get_logger, setup_logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update, text, func

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

    async def upsert_session_stats(self, payload: Dict[str, Any]) -> None:
        """
        Idempotentne uloží summary pre session_id.
        Ak záznam existuje, spraví UPDATE (napr. ak to pošleš 2x).
        """
        sid = _s(payload.get("session_id"))
        if not sid:
            log.info("upsert_session_stats: missing session_id")
            return

        values = {
            "session_id": sid,
            "started_at_ms": _i(payload.get("started_at_ms")),
            "ended_at_ms": _i(payload.get("ended_at_ms")),
            "reconnect_count": _i(payload.get("reconnect_count")) or 0,
            "total_downtime_ms": _i(payload.get("total_downtime_ms")) or 0,
        }

        async with self._sf() as s:
            stmt = insert(SessionStats).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["session_id"],
                set_={
                    "started_at_ms": stmt.excluded.started_at_ms,
                    "ended_at_ms": stmt.excluded.ended_at_ms,
                    "reconnect_count": stmt.excluded.reconnect_count,
                    "total_downtime_ms": stmt.excluded.total_downtime_ms,
                    "updated_at": func.now(),
                },
            )
            await s.execute(stmt)
            await s.commit()


def _extract_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Bezpečne vytiahne hodnoty z vnoreného JSONu do plochej mapy stĺpcov."""
    log.info("Extracting fields from data")
    radio = data.get("radio") or {}
    pos = data.get("position") or {}

    return {
        "Id": data.get("id"),
        "Timestamp": data.get("timestamp_sent"),
        "Latitude": _f(pos.get("lat")),
        "Longitude": _f(pos.get("lon")),
        "Speed": _f(pos.get("speed_kmh")),
        "Level": _i(radio.get("rsrp")),
        "Qual": _i(radio.get("rsrq")),
        "SNR": _i(radio.get("sinr")),
        "CellID": _i(radio.get("cell_id")),
        "NetworkTech": _s(radio.get("network_type")),
        "SessionId": _s(data.get("session_id")),
        "NetworkMode": _s(data.get("network_mode")),
        "LTERSSI": _i(data.get("lte_rssi")),
        "CGI": _s(data.get("cgi")),
        "SERVINGTIME": _i(data.get("serving_time_ms")),
        "BAND": _s(data.get("band")),
        "BANDWIDTH": _i(data.get("bandwidth_mhz")),

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
