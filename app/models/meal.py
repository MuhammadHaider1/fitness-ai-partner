import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Meal(Base):
    __tablename__ = "meals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False ,index=True)

    # Raw input - ("2 roti aur daal khai")
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

     # Structured fields — manual entry ya agent-parsed dono se aa sakte hain
    food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    meal_type: Mapped[str | None] = mapped_column(String(20), nullable=True) #breakfast, lunch, dinner, snack
    calories: Mapped[float] = mapped_column(Float, nullable=False)
    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fats_g: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Agent or Manual Socurce Track
    source: Mapped[str | None] = mapped_column(String(20),default="manual", nullable=False) #manual, agent

    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
