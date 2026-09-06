import uuid
from datetime import datetime
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class WorkoutRoutine(Base):
    __tablename__ = "workout_routines"
    __table_args__ = (UniqueConstraint('user_id', 'day_of_week', name='unique_user_routine_day'),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # 0 = Monday, 1 = Tuesday ... 6 = Sunday (ISO weekday)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    exercises: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())