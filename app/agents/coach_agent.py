from typing import cast

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from app.core.config import settings
from app.models.daily_log import DailyLog
from app.models.meal import Meal
from app.models.workout import Workout

load_dotenv()



class DailyCoachInsight(BaseModel):
    summary: str = Field(description="One or two friendly sentences summarizing the day's performance")
    highlights: list[str] = Field(description="2-4 short positive or notable points, e.g. 'Protein target hit', 'On a 3-day streak'")
    suggestions: list[str] = Field(description="1-3 short, actionable suggestions for improvement, if any. Empty list if nothing notable to suggest.")


def build_coach_prompt(
    daily_log: DailyLog,
    meals: list[Meal],
    workouts: list[Workout],
    current_streak: int,
) -> str:
    
    meals_summary = "\n".join(
        f"{m.food_name} ({m.meal_type or 'unspecified'}): {m.calories} kcal, {m.protein_g}g protein"
        for m in meals
    ) or "No meals logged."

    workouts_summary = "\n".join(
        f"{w.name} ({w.workout_type}): {w.calories_burned} kcal burned, intensity: {w.intensity}"
        for w in workouts
    ) or "No workouts logged."


    return f"""You are a friendly, encouraging fitness coach reviewing a user's day.

Date: {daily_log.log_date}
Calorie target: {daily_log.calorie_target if daily_log.calorie_target else "not set"}
Total calories consumed: {daily_log.total_calories}
Total protein: {daily_log.total_protein_g}g, carbs: {daily_log.total_carbs_g}g, fats: {daily_log.total_fats_g}g
Total calories burned (exercise): {daily_log.total_calories_burned}
Water intake: {daily_log.water_intake_ml}ml
Mood: {daily_log.mood or "not logged"}
Current on-target streak: {current_streak} day(s)

Meals logged:
{meals_summary}

Workouts logged:
{workouts_summary}

Give a warm, brief, encouraging review. Be specific with numbers where relevant. Do not repeat all the raw data back — synthesize it into useful insight. If data is missing (no meals/workouts), gently note that instead of inventing numbers.
"""

async def generate_daily_coach_insight(
    daily_log: DailyLog,
    meals: list[Meal],
    workouts: list[Workout],
    current_streak: int,
) -> DailyCoachInsight:
    prompt = build_coach_prompt(daily_log, meals, workouts, current_streak)

    # 1. Initialize the LLM fresh inside the active event loop scope
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.4,
    )

    # 2. Bind structured output dynamically
    structured_llm = llm.with_structured_output(DailyCoachInsight)

    
    result = await structured_llm.ainvoke(prompt)
    return cast(DailyCoachInsight ,result)



class WeeklyCoachInsight(BaseModel):
    summary: str = Field(description="2-3 sentence overview of the week's performance")
    highlights: list[str] = Field(description="2-5 notable wins or patterns from the week")
    suggestions: list[str] = Field(description="1-3 actionable suggestions for next week")


def build_weekly_prompt(week_start, week_end, daily_summary, meals_count: int, workouts_count: int) -> str:
    return f"""You are a friendly, encouraging fitness coach reviewing a user's WEEK.

Week: {week_start} to {week_end}
Days logged: {daily_summary.days_logged}
Days on calorie target: {daily_summary.days_on_target}
Average daily calories: {daily_summary.average_calories}
Average protein: {daily_summary.average_protein_g}g, carbs: {daily_summary.average_carbs_g}g, fats: {daily_summary.average_fats_g}g
Current streak: {daily_summary.current_streak} day(s)
Total meals logged this week: {meals_count}
Total workouts logged this week: {workouts_count}

Give a warm, brief weekly review. Point out patterns (consistency, trends), celebrate wins, and give 1-3 concrete suggestions for the upcoming week. Do not just repeat the numbers — synthesize them into insight.
"""


async def generate_weekly_coach_insight(week_start, week_end, daily_summary, meals_count: int, workouts_count: int) -> WeeklyCoachInsight:
    prompt = build_weekly_prompt(week_start, week_end, daily_summary, meals_count, workouts_count)

    llm = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.4,
        )
    weekly_structured_llm = llm.with_structured_output(WeeklyCoachInsight)
    
    result = await weekly_structured_llm.ainvoke(prompt)
    return cast(WeeklyCoachInsight, result)