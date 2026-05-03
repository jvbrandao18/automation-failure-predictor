from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExecutionRecord(Base):
    __tablename__ = "execution_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    automation_name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    duration_seconds: Mapped[float] = mapped_column(Float)
    retry_count: Mapped[int] = mapped_column(Integer)
    error_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    environment: Mapped[str] = mapped_column(String(20), index=True)

    risk_score: Mapped[int] = mapped_column(Integer, index=True)
    risk_level: Mapped[str] = mapped_column(String(20), index=True)
    probable_causes: Mapped[list[str]] = mapped_column(JSON)
    recommended_actions: Mapped[list[str]] = mapped_column(JSON)
    explanation: Mapped[str] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
