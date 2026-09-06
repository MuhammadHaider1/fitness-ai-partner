import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (UniqueConstraint('user_id', 'log_date', name='unique_user_log_date'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False ,index=True)

    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Goal — user set karega (ya profile se calculate hoga baad mein)
    calorie_target: Mapped[float | None] = mapped_column(Float, nullable=True)

      # Actual — meals se accumulate hoga
    total_calories: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    total_protein_g: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    total_carbs_g: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    total_fats_g: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    water_intake_ml: Mapped[float | None] = mapped_column(Float, default=0, nullable=True)
    mood: Mapped[str | None] = mapped_column(String(50), nullable=True) # e.g. "good", "tired", "low"
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_calories_burned: Mapped[float] = mapped_column(Float, default=0, nullable=False)


    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())

