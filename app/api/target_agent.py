from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.target_agent import suggest_target, user_metrics
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.daily_log import DailyLogRead, DailyLogUpdate
from app.schemas.target import ApplyTargetRequest, SuggestedTargetResponse
from app.services.daily_log_service import update_daily_log

router = APIRouter(prefix="/coach", tags=["coach"])


@router.get("/suggest-target", response_model=SuggestedTargetResponse, status_code=status.HTTP_200_OK)
async def get_suggested_target(current_user: User = Depends(get_current_user)):
    try:
        result = await suggest_target(current_user)
        metrics = user_metrics(current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI is busy right now (Gemini rate limit reached). Please try again in a minute.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Target suggestion failed. Please try again.",
        )

    return SuggestedTargetResponse(
        calorie_target=result.calorie_target,
        protein_target_g=result.protein_target_g,
        carbs_target_g=result.carbs_target_g,
        fats_target_g=result.fats_target_g,
        bmr=metrics["bmr"],
        tdee=metrics["tdee"],
        bmi=metrics["bmi"],
        reasoning=result.reasoning,
    )


@router.post("/apply-target", response_model=DailyLogRead, status_code=status.HTTP_200_OK)
async def apply_target(
    payload: ApplyTargetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Suggested target ko aaj ki daily-log par as calorie target apply karta hai."""
    from datetime import date

    update_in = DailyLogUpdate(calorie_target=payload.calorie_target)
    today = date.today()
    try:
        return await update_daily_log(db, current_user.id, today, update_in)
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI is busy right now (Gemini rate limit reached). Please try again in a minute.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Target apply nahi ho saka. Please try again.",
        )