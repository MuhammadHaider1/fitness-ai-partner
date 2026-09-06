from pydantic import BaseModel


class SuggestedTargetResponse(BaseModel):
    calorie_target: float
    protein_target_g: float
    carbs_target_g: float
    fats_target_g: float
    bmr: float
    tdee: float
    bmi: float
    reasoning: str


class ApplyTargetRequest(BaseModel):
    calorie_target: float
    protein_target_g: float | None = None
    carbs_target_g: float | None = None
    fats_target_g: float | None = None