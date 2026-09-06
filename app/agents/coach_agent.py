from typing import cast

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.core.llm import get_llm, json_schema_instruction
from app.models.daily_log import DailyLog
from app.models.meal import Meal
from app.models.user import User
from app.models.workout import Workout
from app.services.body_metrics import body_metrics, local_targets

load_dotenv()


class DailyCoachInsight(BaseModel):
    summary: str = Field(description="One or two friendly sentences summarizing the day's performance")
    highlights: list[str] = Field(description="2-4 short positive or notable points, e.g. 'Protein target hit', 'On a 3-day streak'")
    suggestions: list[str] = Field(description="1-3 short, actionable suggestions for improvement, if any. Empty list if nothing notable to suggest.")


def profile_context(user: User) -> str:
    if user.weight_kg is None or user.height_cm is None or user.age is None or user.gender is None:
        return "User profile incomplete (age/height/weight/gender) — no body metrics available. Be general but helpful."

    metrics = body_metrics(user.age, user.height_cm, user.weight_kg, user.gender, user.activity_level)
    targets = local_targets(metrics["tdee"], user.weight_kg, user.goal)
    return (
        f"User profile:\n"
        f"- Age: {user.age}, Gender: {user.gender}\n"
        f"- Height: {user.height_cm} cm, Weight: {user.weight_kg} kg\n"
        f"- Goal: {user.goal or 'maintenance'}, Activity level: {user.activity_level or 'moderate'}\n"
        f"- BMR: {metrics['bmr']} kcal\n"
        f"- TDEE: {metrics['tdee']} kcal (maintenance calories from this profile)\n"
        f"- BMI: {metrics['bmi']}\n"
        f"- Suggested daily targets (from profile): ~{targets['calorie_target']} kcal, "
        f"protein {targets['protein_target_g']}g, carbs {targets['carbs_target_g']}g, fats {targets['fats_target_g']}g"
    )


def build_coach_prompt(
    daily_log: DailyLog,
    meals: list[Meal],
    workouts: list[Workout],
    current_streak: int,
    user: User,
) -> str:
    meals_summary = "\n".join(
        f"{m.food_name} ({m.meal_type or 'unspecified'}): {m.calories} kcal, {m.protein_g}g protein"
        for m in meals
    ) or "No meals logged."

    workouts_summary = "\n".join(
        f"{w.name} ({w.workout_type}): {w.calories_burned} kcal burned, intensity: {w.intensity}"
        for w in workouts
    ) or "No workouts logged."

    profile = profile_context(user)
    consumed = daily_log.total_calories
    target = daily_log.calorie_target

    target_vs_profile = ""
    if target is None or target == 0:
        target_vs_profile = "(No calorie target set for today — compare their intake against their profile-based TDEE and suggest setting a target.)"
    else:
        diff = round(consumed - target)
        target_vs_profile = f"Their log target: {target} kcal. Difference today: {diff:+} kcal vs target."

    return f"""You are a friendly, encouraging fitness coach reviewing a user's day. You have their body-profile metrics — use them to make the advice personal.

{profile}

Today's log:
Date: {daily_log.log_date}
Total calories consumed: {consumed}
Total protein: {daily_log.total_protein_g}g, carbs: {daily_log.total_carbs_g}g, fats: {daily_log.total_fats_g}g
Total calories burned (exercise): {daily_log.total_calories_burned}
Water intake: {daily_log.water_intake_ml}ml
Mood: {daily_log.mood or "not logged"}
Current on-target streak: {current_streak} day(s)
{target_vs_profile}

Meals logged:
{meals_summary}

Workouts logged:
{workouts_summary}

Give a warm, brief, encouraging review. Be specific with numbers where relevant and reference their BMR/TDEE/BMI and targets to make it personal (e.g. 'your maintenance is ~X kcal'). Do not repeat all the raw data back — synthesize it into useful insight. If data is missing (no meals/workouts), gently note that instead of inventing numbers.

{json_schema_instruction(DailyCoachInsight)}
"""


async def generate_daily_coach_insight(
    daily_log: DailyLog,
    meals: list[Meal],
    workouts: list[Workout],
    current_streak: int,
    user: User,
) -> DailyCoachInsight:
    prompt = build_coach_prompt(daily_log, meals, workouts, current_streak, user)

    llm = get_llm(temperature=0.4)

    structured_llm = llm.with_structured_output(DailyCoachInsight, method="json_mode")

    result = await structured_llm.ainvoke(prompt)
    return cast(DailyCoachInsight, result)


class WeeklyCoachInsight(BaseModel):
    summary: str = Field(description="2-3 sentence overview of the week's performance")
    highlights: list[str] = Field(description="2-5 notable wins or patterns from the week")
    suggestions: list[str] = Field(description="1-3 actionable suggestions for next week")


def build_weekly_prompt(week_start, week_end, daily_summary, meals_count: int, workouts_count: int, user: User) -> str:
    profile = profile_context(user)
    return f"""You are a friendly, encouraging fitness coach reviewing a user's WEEK.

{profile}

Week: {week_start} to {week_end}
Days logged: {daily_summary.days_logged}
Days on calorie target: {daily_summary.days_on_target}
Average daily calories: {daily_summary.average_calories}
Average protein: {daily_summary.average_protein_g}g, carbs: {daily_summary.average_carbs_g}g, fats: {daily_summary.average_fats_g}g
Current streak: {daily_summary.current_streak} day(s)
Total meals logged this week: {meals_count}
Total workouts logged this week: {workouts_count}

Give a warm, brief weekly review. Point out patterns (consistency, trends), celebrate wins, and give 1-3 concrete suggestions for the upcoming week. Reference their profile metrics (BMR/TDEE/BMI, targets) to make it personal, e.g. how their average intake compares to their maintenance. Do not just repeat the numbers — synthesize them into insight.

{json_schema_instruction(WeeklyCoachInsight)}
"""


async def generate_weekly_coach_insight(week_start, week_end, daily_summary, meals_count: int, workouts_count: int, user: User) -> WeeklyCoachInsight:
    prompt = build_weekly_prompt(week_start, week_end, daily_summary, meals_count, workouts_count, user)

    llm = get_llm(temperature=0.4)
    weekly_structured_llm = llm.with_structured_output(WeeklyCoachInsight, method="json_mode")

    result = await weekly_structured_llm.ainvoke(prompt)
    return cast(WeeklyCoachInsight, result)


async def chat_with_coach(user: User, message: str, context_rows: list[str]) -> str:
    profile = profile_context(user)
    recent = "\n".join(context_rows) or "No recent logs available."
    prompt = (
        "You are a friendly, knowledgeable personal AI fitness coach. Answer the user's question "
        "helpfully and concisely (2-6 sentences, or a short bulleted list when useful). Base your advice "
        "on their profile numbers where relevant. Never invent numbers you don't know — use their "
        "BMR/TDEE/suggested targets as estimates and say so when you are estimating.\n\n"
        f"{profile}\n\n"
        f"Recent activity (last few days):\n{recent}\n\n"
        f"User asks: {message}"
    )

    llm = get_llm(temperature=0.5)

    result = await llm.ainvoke(prompt)
    return str(result.content)