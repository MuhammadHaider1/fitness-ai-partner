from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.coach_agent import generate_daily_coach_insight
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.coach import DailyCoachResponse
from app.services.daily_log_service import get_daily_log, get_daily_log_summary
from app.services.meal_service import get_meals_by_user
from app.services.workout_service import get_workouts_by_user

router = APIRouter(prefix="/coach", tags=["coach"])


@router.get("/daily", response_model=DailyCoachResponse)
async def get_daily_coach_feedback(
    log_date: date = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    daily_log = await get_daily_log(db, current_user.id, log_date)
    meals = await get_meals_by_user(db, current_user.id, log_date)
    workouts = await get_workouts_by_user(db, current_user.id, log_date)

    # Current streak nikalne ke liye pichle 30 din ka summary use karte hain
    summary = await get_daily_log_summary(db, current_user.id, log_date - timedelta(days=30), log_date)

    insight = await generate_daily_coach_insight(daily_log, meals, workouts, summary.current_streak)

    return DailyCoachResponse(
        log_date=log_date,
        summary=insight.summary,
        highlights=insight.highlights,
        suggestions=insight.suggestions,
    )