from fastapi import APIRouter, Depends, HTTPException, status

from app.agents.target_agent import suggest_target
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.target import SuggestedTargetResponse

router = APIRouter(prefix="/coach", tags=["coach"])


@router.get("/suggest-target", response_model=SuggestedTargetResponse , status_code=status.HTTP_200_OK)
async def get_suggested_target(current_user: User = Depends(get_current_user)):
    try:
        result = await suggest_target(current_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return SuggestedTargetResponse(
        calorie_target=result.calorie_target,
        protein_target_g=result.protein_target_g,
        carbs_target_g=result.carbs_target_g,
        fats_target_g=result.fats_target_g,
        reasoning=result.reasoning,
    )