# models.py
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Boolean, String, Float, Integer, BigInteger, DateTime, func


class Base(DeclarativeBase):
    pass


class Measurement(Base):
    __tablename__ = "measurements"

    Id: Mapped[str] = mapped_column(String, primary_key=True)

    SessionId: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True)

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
    Outage: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    RTT_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class SessionStats(Base):
    __tablename__ = "session_stats"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)

    started_at_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)

    ended_at_ms: Mapped[int] = mapped_column(BigInteger, nullable=True)

    reconnect_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0)

    total_downtime_ms: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
