from typing import cast

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.models.user import User


class SuggestedTarget(BaseModel):
    calorie_target: float = Field(description="Recommended daily calorie target")
    protein_target_g: float = Field(description="Recommended daily protein target in grams")
    carbs_target_g: float = Field(description="Recommended daily carbs target in grams")
    fats_target_g: float = Field(description="Recommended daily fats target in grams")
    reasoning: str = Field(description="Brief explanation of how this was calculated, mentioning BMR/TDEE and the goal")


def calculate_bmr(age: int, height_cm: float, weight_kg: float, gender: str) -> float:
    """Mifflin-St Jeor equation — ek standard, widely-trusted BMR formula"""
    if gender.lower() == "male":
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

def calculate_tdee(bmr: float, activity_level: str | None) -> float:
    multiplier = ACTIVITY_MULTIPLIERS.get((activity_level or "moderate").lower().replace(" ", "_"), 1.55)
    return bmr * multiplier


def build_target_prompt(user: User, bmr: float, tdee: float) -> str:
    return f"""You are a fitness nutrition expert. Recommend a daily calorie and macro target for this user.

Age: {user.age}
Height: {user.height_cm} cm
Weight: {user.weight_kg} kg
Gender: {user.gender}
Goal: {user.goal or "not specified — assume general health/maintenance"}
Activity level: {user.activity_level or "moderate"}

Calculated BMR (Basal Metabolic Rate): {bmr:.0f} kcal
Calculated TDEE (Total Daily Energy Expenditure): {tdee:.0f} kcal

Based on their goal:
- If goal is weight loss / cutting / fat loss: suggest a moderate deficit (~15-20% below TDEE)
- If goal is muscle gain / bulking: suggest a moderate surplus (~10-15% above TDEE)
- If goal is body recomposition: suggest a small deficit of 300-400 kcal below TDEE (a common evidence-based approach for simultaneous fat loss and muscle retention/gain)
- If goal is maintenance / not specified: suggest close to TDEE

Also recommend protein (higher for muscle gain/recomp, ~1.6-2.2g per kg bodyweight), and reasonable carbs/fats to fill the remaining calories.

Give practical, realistic numbers — not extreme values.
"""

async def suggest_target(user: User) -> SuggestedTarget:
    if not all([user.age, user.height_cm, user.weight_kg, user.gender]):
        raise ValueError("User profile incomplete — age, height_cm, weight_kg, and gender are required for target suggestion")

    # Ab Pylance ko explicitly batao ke ye fields None nahi hain (humne upar check kar liya hai)
    assert user.age is not None
    assert user.height_cm is not None
    assert user.weight_kg is not None
    assert user.gender is not None

    bmr = calculate_bmr(user.age, user.height_cm, user.weight_kg, user.gender)
    tdee = calculate_tdee(bmr, user.activity_level)

    prompt = build_target_prompt(user, bmr, tdee)

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.3,
    )
    structured_llm = llm.with_structured_output(SuggestedTarget)

    result = await structured_llm.ainvoke(prompt)
    return cast(SuggestedTarget, result)