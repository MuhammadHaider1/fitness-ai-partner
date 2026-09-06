from pydantic import BaseModel

from app.schemas.meal import MealDraft
from app.schemas.workout import WorkoutDraft


class EntryCreateFromText(BaseModel):
    raw_text: str


class EntryDraft(BaseModel):
    intent: str  # "meal" or "workout"
    meal_draft: MealDraft | None = None
    workout_draft: WorkoutDraft | None = None