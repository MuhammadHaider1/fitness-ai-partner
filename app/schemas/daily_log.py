import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DailyLogUpdate(BaseModel):
    """User ye fields set/update kar sakta hai"""
    calorie_target: float | None = None
    water_intake_ml: float | None = 0
    mood: str | None = None
    notes: str | None = None


class DailyLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    log_date: date
    calorie_target: float | None
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fats_g: float
    total_calories_burned: float 
    water_intake_ml: float
    mood: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime | None


class DailyLogSummary(BaseModel):
    start_date: date
    end_date: date
    days_logged: int
    days_on_target: int
    average_calories: float
    average_protein_g: float
    average_carbs_g: float
    average_fats_g: float
    current_streak: int