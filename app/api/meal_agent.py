from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.nutrition_agent import adjust_meal_draft
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.meal import MealAdjustRequest, MealCreate, MealDraft, MealRead
from app.services.meal_service import create_meal

router = APIRouter(prefix="/agent/meals", tags=["agent-meals"])


@router.post("/adjust", response_model=MealDraft)
async def adjust_meal(
    payload: MealAdjustRequest,
    current_user: User = Depends(get_current_user),
):
    parsed = await adjust_meal_draft(payload.previous_draft, payload.adjustment_text)
    return MealDraft(
        is_confident=parsed.is_confident,
        clarification_question=parsed.clarification_question,
        food_name=parsed.food_name or payload.previous_draft.food_name,
        meal_type=parsed.meal_type or payload.previous_draft.meal_type,
        calories=parsed.calories,
        protein_g=parsed.protein_g,
        carbs_g=parsed.carbs_g,
        fats_g=parsed.fats_g,
        reasoning=parsed.reasoning,
        raw_text=payload.previous_draft.raw_text,
    )


@router.post("/confirm", response_model=MealRead, status_code=status.HTTP_201_CREATED)
async def confirm_meal(
    meal_in: MealCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_meal(db, current_user.id, meal_in, source="agent")