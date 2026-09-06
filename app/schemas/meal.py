import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MealBase(BaseModel):
    food_name: str
    meal_type: str | None = None
    calories: float
    protein_g: float | None = None
    carbs_g: float | None = None
    fats_g: float | None = None


class MealCreate(MealBase):
    """Structured manual entry"""
    pass  # noqa: PIE790


class MealCreateFromText(BaseModel):
    """Natural language entry — agent isko parse karega, koi structured field yahan zaroori nahi"""
    raw_text: str
    meal_type: str | None = None


class MealRead(MealBase):
    id: uuid.UUID
    user_id: uuid.UUID
    raw_text: str | None = None
    source: str
    logged_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class MealUpdate(BaseModel):
    food_name: str | None = None
    meal_type: str | None = None
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fats_g: float | None = None


class MealDraft(BaseModel):
    is_confident: bool
    clarification_question: str | None = None
    food_name: str | None = None
    meal_type: str | None = None
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fats_g: float | None = None
    reasoning: str | None = None
    raw_text: str


class MealAdjustRequest(BaseModel):
    """User ka follow-up message + previous draft context"""
    previous_draft: MealDraft
    adjustment_text: str