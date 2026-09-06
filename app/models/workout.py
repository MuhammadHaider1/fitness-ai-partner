import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True , default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True) , ForeignKey("users.id") ,nullable= False , index=True)

    # Raw input — natural language ("30 min running", "bench press 3 sets 10 reps 60kg")
    raw_text: Mapped[str | None] = mapped_column(Text , nullable=True)

    workout_type: Mapped[str] = mapped_column(String(50) , nullable=False) #'Cardio' , 'Strength' , etc
    name: Mapped[str] = mapped_column(String(255) , nullable=False) #'Running' , 'BenchPress'

    # Cardio-specific fields
    duration_minutes: Mapped[float | None] = mapped_column(Float , nullable= True)
    distance_km: Mapped[float | None] = mapped_column(Float , nullable= True)


    # Strength-specific fields
    sets: Mapped[int | None] = mapped_column(Integer , nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer , nullable=True)
    weight_kg: Mapped[Float | None] = mapped_column(Float , nullable=True)


     # Common fields
    intensity: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "low", "moderate", "high"
    calories_burned: Mapped[float] = mapped_column(Float, nullable=False, default=0)


    source: Mapped[str] = mapped_column(String(20) , default="manual" , nullable=False) #'manual' or 'agent'

    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

