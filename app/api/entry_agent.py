from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.router_agent import parse_entry
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.entry import EntryCreateFromText, EntryDraft
from app.schemas.meal import MealDraft
from app.schemas.workout import WorkoutDraft

router = APIRouter(prefix="/agent", tags=["agent-entry"])


def is_rate_limited(error: Exception) -> bool:
    return "429" in str(error) or "RESOURCE_EXHAUSTED" in str(error)


@router.post("/parse", response_model=EntryDraft)
async def parse_any_entry(
    payload: EntryCreateFromText,
    current_user: User = Depends(get_current_user),
):
    try:
        result = await parse_entry(payload.raw_text)
    except Exception as e:
        if is_rate_limited(e):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI is busy right now (Gemini rate limit reached). Please try again in a minute.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI could not parse your entry. Please try again.",
        )

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