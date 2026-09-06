from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.workout_agent import adjust_workout_draft
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.workout import (
    WorkoutAdjustRequest,
    WorkoutCreate,
    WorkoutDraft,
    WorkoutRead,
)
from app.services.workout_service import create_workout

router = APIRouter(prefix="/agent/workouts", tags=["agent-workouts"])


@router.post("/adjust", response_model=WorkoutDraft)
async def adjust_workout(
    payload: WorkoutAdjustRequest,
    current_user: User = Depends(get_current_user),
):
    parsed = await adjust_workout_draft(payload.previous_draft, payload.adjustment_text)
    return WorkoutDraft(
        is_confident=parsed.is_confident,
        clarification_question=parsed.clarification_question,
        workout_type=parsed.workout_type or payload.previous_draft.workout_type,
        name=parsed.name or payload.previous_draft.name,
        duration_minutes=parsed.duration_minutes,
        distance_km=parsed.distance_km,
        sets=parsed.sets,
        reps=parsed.reps,
        weight_kg=parsed.weight_kg,
        intensity=parsed.intensity,
        calories_burned=parsed.calories_burned,
        reasoning=parsed.reasoning,
        raw_text=payload.previous_draft.raw_text,
    )


@router.post("/confirm", response_model=WorkoutRead, status_code=status.HTTP_201_CREATED)
async def confirm_workout(
    workout_in: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_workout(db, current_user.id, workout_in, source="agent")