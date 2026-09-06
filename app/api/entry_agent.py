from fastapi import APIRouter, Depends

from app.agents.router_agent import parse_entry
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.entry import EntryCreateFromText, EntryDraft
from app.schemas.meal import MealDraft
from app.schemas.workout import WorkoutDraft

router = APIRouter(prefix="/agent", tags=["agent-entry"])


@router.post("/parse", response_model=EntryDraft)
async def parse_any_entry(
    payload: EntryCreateFromText,
    current_user: User = Depends(get_current_user),
):
    result = await parse_entry(payload.raw_text)

    if result["intent"] == "meal":
        parsed = result["parsed_meal"]
        return EntryDraft(
            intent="meal",
            meal_draft=MealDraft(
                is_confident=parsed.is_confident,
                clarification_question=parsed.clarification_question,
                food_name=parsed.food_name,
                meal_type=parsed.meal_type,
                calories=parsed.calories,
                protein_g=parsed.protein_g,
                carbs_g=parsed.carbs_g,
                fats_g=parsed.fats_g,
                reasoning=parsed.reasoning,
                raw_text=payload.raw_text,
            ),
        )

    parsed = result["parsed_workout"]
    return EntryDraft(
        intent="workout",
        workout_draft=WorkoutDraft(
            is_confident=parsed.is_confident,
            clarification_question=parsed.clarification_question,
            workout_type=parsed.workout_type,
            name=parsed.name,
            duration_minutes=parsed.duration_minutes,
            distance_km=parsed.distance_km,
            sets=parsed.sets,
            reps=parsed.reps,
            weight_kg=parsed.weight_kg,
            intensity=parsed.intensity,
            calories_burned=parsed.calories_burned,
            reasoning=parsed.reasoning,
            raw_text=payload.raw_text,
        ),
    )