ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def calculate_bmr(age: int, height_cm: float, weight_kg: float, gender: str) -> float:
    """Mifflin-St Jeor equation — standard BMR formula"""
    if (gender or "").lower() == "male":
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161


def calculate_tdee(bmr: float, activity_level: str | None) -> float:
    multiplier = ACTIVITY_MULTIPLIERS.get(
        (activity_level or "moderate").lower().replace(" ", "_"), 1.55
    )
    return bmr * multiplier


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """BMI = weight(kg) / height(m)^2"""
    if height_cm and height_cm > 0:
        return weight_kg / ((height_cm / 100) ** 2)
    return 0.0


def body_metrics(age, height_cm, weight_kg, gender, activity_level) -> dict:
    bmr = calculate_bmr(age, height_cm, weight_kg, gender)
    tdee = calculate_tdee(bmr, activity_level)
    bmi = round(calculate_bmi(weight_kg, height_cm), 1)
    return {"bmr": round(bmr), "tdee": round(tdee), "bmi": bmi}


def local_targets(tdee: float, weight_kg: float, goal: str | None) -> dict:
    """Gemini ke bina hi ek evidence-based calorie/macro target estimate."""
    goal = (goal or "maintenance").lower().replace(" ", "_")
    if goal in ("weight_loss", "cutting", "fat_loss", "lose_weight"):
        intake = round(tdee * 0.82)
    elif goal in ("muscle_gain", "bulking", "gain_muscle"):
        intake = round(tdee * 1.12)
    elif goal == "recomp":
        intake = round(tdee - 350)
    else:
        intake = round(tdee)

    protein = round(weight_kg * 1.8)          # g/day, muscle-friendly
    fat = round((intake * 0.25) / 9)          # 25% calories from fat
    carbs = round((intake - (protein * 4) - (fat * 9)) / 4)
    return {
        "calorie_target": intake,
        "protein_target_g": protein,
        "carbs_target_g": max(carbs, 0),
        "fats_target_g": fat,
    }