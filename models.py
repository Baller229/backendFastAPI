# models.py
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer, BigInteger, DateTime, func

class Base(DeclarativeBase):
    pass

class Measurement(Base):
    __tablename__ = "measurements"

    # Primárny kľúč od klienta (napr. "m123")
    id: Mapped[str] = mapped_column(String, primary_key=True)

    # Čas odoslania z klienta v ms (wall-clock z mobilu)
    timestamp_ms: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Poloha
    lat: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lon: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    speed_kmh: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Rádiové metriky
    rsrp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rsrq: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sinr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cell_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    network_type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # Zariadenie
    operator: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # V2X – len typ, payload si rieš mimo (ak chceš vôbec)
    v2x_kind: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # RTT dopĺňané neskôr idempotentne
    rtt_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Serverová pečiatka
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
