import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkoutBase(BaseModel):
    workout_type: str  # "cardio" or "strength"
    name: str
    duration_minutes: float | None = None
    distance_km: float | None = None
    sets: int | None = None
    reps: int | None = None
    weight_kg: float | None = None
    intensity: str | None = None  # "low", "moderate", "high"
    calories_burned: float


class WorkoutCreate(WorkoutBase):
    """Structured manual entry"""
    pass  # noqa: PIE790


class WorkoutUpdate(BaseModel):
    """Sab fields optional — sirf jo change karna ho wahi bheje"""
    workout_type: str | None = None
    name: str | None = None
    duration_minutes: float | None = None
    distance_km: float | None = None
    sets: int | None = None
    reps: int | None = None
    weight_kg: float | None = None
    intensity: str | None = None
    calories_burned: float | None = None


class WorkoutCreateFromText(BaseModel):
    """Natural language entry — agent isko parse karega"""
    raw_text: str


class WorkoutRead(WorkoutBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    raw_text: str | None = None
    source: str
    logged_at: datetime
    created_at: datetime

class WorkoutDraft(BaseModel):
    is_confident: bool
    clarification_question: str | None = None
    workout_type: str | None = None
    name: str | None = None
    duration_minutes: float | None = None
    distance_km: float | None = None
    sets: int | None = None
    reps: int | None = None
    weight_kg: float | None = None
    intensity: str | None = None
    calories_burned: float | None = None
    reasoning: str | None = None
    raw_text: str


class WorkoutAdjustRequest(BaseModel):
    previous_draft: WorkoutDraft
    adjustment_text: str
    