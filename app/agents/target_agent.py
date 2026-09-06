from typing import cast

from pydantic import BaseModel, Field

from app.core.llm import get_llm, json_schema_instruction
from app.models.user import User
from app.services.body_metrics import (
    body_metrics,
    local_targets,
)


class SuggestedTarget(BaseModel):
    calorie_target: float = Field(description="Recommended daily calorie target")
    protein_target_g: float = Field(description="Recommended daily protein target in grams")
    carbs_target_g: float = Field(description="Recommended daily carbs target in grams")
    fats_target_g: float = Field(description="Recommended daily fats target in grams")
    reasoning: str = Field(description="Brief explanation of how this was calculated, mentioning BMR/TDEE/BMI and the goal")
    source: str = Field(default="ai", description="ai = machine-generated, math = plain formula estimate")


def build_target_prompt(user: User, metrics: dict, hint: dict) -> str:
    return f"""You are a fitness nutrition expert. Recommend a daily calorie and macro target for this user.

Age: {user.age}
Height: {user.height_cm} cm
Weight: {user.weight_kg} kg
Gender: {user.gender}
Goal: {user.goal or "not specified — assume general health/maintenance"}
Activity level: {user.activity_level or "moderate"}

Calculated body metrics (from their profile):
- BMR (Basal Metabolic Rate): {metrics['bmr']} kcal
- TDEE (Total Daily Energy Expenditure): {metrics['tdee']} kcal
- BMI: {metrics['bmi']}

Based on their goal:
- If goal is weight loss / cutting / fat loss: suggest a moderate deficit (~15-20% below TDEE)
- If goal is muscle gain / bulking: suggest a moderate surplus (~10-15% above TDEE)
- If goal is body recomposition: suggest a small deficit of 300-400 kcal below TDEE (a common evidence-based approach for simultaneous fat loss and muscle retention/gain)
- If goal is maintenance / not specified: suggest close to TDEE

Also recommend protein (higher for muscle gain/recomp, ~1.6-2.2g per kg bodyweight), and reasonable carbs/fats to fill the remaining calories.

A plain math estimate is: {hint['calorie_target']} kcal, protein {hint['protein_target_g']}g, carbs {hint['carbs_target_g']}g, fats {hint['fats_target_g']}g.
Use it as a sanity baseline and give practical, realistic rounded numbers — not extreme values.

{json_schema_instruction(SuggestedTarget)}
"""


def user_metrics(user: User) -> dict:
    """Complete safe wrapper — returns metrics dict or raises ValueError if profile incomplete."""
    if not all([user.age, user.height_cm, user.weight_kg, user.gender]):
        raise ValueError("User profile incomplete — age, height_cm, weight_kg, and gender are required for target suggestion")
    return body_metrics(user.age, user.height_cm, user.weight_kg, user.gender, user.activity_level)


def math_fallback(user: User, metrics: dict) -> SuggestedTarget:
    """Direct formula estimate — reliable targets without AI."""
    hint = local_targets(metrics["tdee"], user.weight_kg, user.goal)
    goal = (user.goal or "maintenance").replace("_", " ").capitalize()
    reasoning = (
        f"The AI service was momentarily unavailable, so these targets were calculated directly from your profile: "
        f"BMR {metrics['bmr']} kcal, TDEE {metrics['tdee']} kcal, BMI {metrics['bmi']}. "
        f"Based on your goal ({goal}), a daily intake of {hint['calorie_target']} kcal is suggested, "
        f"with protein at {hint['protein_target_g']}g (1.8g/kg for muscle retention). "
        f"You'll get a more personalized estimate once the AI is available."
    )
    return SuggestedTarget(
        calorie_target=hint["calorie_target"],
        protein_target_g=hint["protein_target_g"],
        carbs_target_g=hint["carbs_target_g"],
        fats_target_g=hint["fats_target_g"],
        reasoning=reasoning,
        source="math",
    )


async def suggest_target(user: User) -> SuggestedTarget:
    metrics = user_metrics(user)
    hint = local_targets(metrics["tdee"], user.weight_kg, user.goal)
    prompt = build_target_prompt(user, metrics, hint)

    llm = get_llm(temperature=0.3)
    structured_llm = llm.with_structured_output(SuggestedTarget, method="json_mode")

    try:
        result = await structured_llm.ainvoke(prompt)
    except Exception:
        # Gemini unavailable / rate-limited → reliable math fallback, never a hard failure
        return math_fallback(user, metrics)

    result.source = "ai"
    return cast(SuggestedTarget, result)