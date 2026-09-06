from pydantic import BaseModel


class SuggestedTargetResponse(BaseModel):
    calorie_target: float
    protein_target_g: float
    carbs_target_g: float
    fats_target_g: float
    reasoning: str