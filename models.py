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
    Id: Mapped[str] = mapped_column(String, primary_key=True)

    SessionId: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True)

    # Čas odoslania z klienta v ms (wall-clock z mobilu)
    Timestamp: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True)

    # GPS
    Latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    Longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    Speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Rádiové metriky
    Level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    Qual: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    SNR: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    CellID: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    NetworkTech: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True)

    # New fields
    NetworkMode: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    LTERSSI: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    CGI: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    SERVINGTIME: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True)
    BAND: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    BANDWIDTH: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # V2X – len typ, payload si rieš mimo (ak chceš vôbec)
    # V2X_KIND: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    # RTT dopĺňané neskôr idempotentne
    RTT_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class SessionStats(Base):
    __tablename__ = "session_stats"

    # Primárny kľúč od klienta (napr. "s123")
    session_id: Mapped[str] = mapped_column(String, primary_key=True)

    started_at_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)

    ended_at_ms: Mapped[int] = mapped_column(BigInteger, nullable=True)

    # Počet meraní v session
    reconnect_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)

    total_downtime_ms: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
