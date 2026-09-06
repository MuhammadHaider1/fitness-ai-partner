import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class RoutineExercise(BaseModel):
    name: str = Field(..., min_length=1)
    workout_type: str = "strength"   # strength | cardio
    sets: int | None = None
    reps: int | None = None
    weight_kg: float | None = None
    duration_minutes: float | None = None
    distance_km: float | None = None
    intensity: str | None = None     # low | moderate | high
    calories_burned: float | None = None


class WorkoutRoutineDayUpdate(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)  # 0=Monday ... 6=Sunday
    exercises: list[RoutineExercise] = []


class WorkoutRoutineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    day_of_week: int
    exercises: list[dict]
    created_at: datetime
    updated_at: datetime | None