import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.coach_agent import generate_weekly_coach_insight
from app.core.config import settings
from app.models.user import User
from app.models.weekly_report import WeeklyReport
from app.services.daily_log_service import get_daily_log_summary


async def generate_and_save_weekly_report(db: AsyncSession, user: User, week_start: date, week_end: date) -> WeeklyReport:
    user_id = user.id
    daily_summary = await get_daily_log_summary(db, user_id, week_start, week_end)

    # Poore hafte ki meals/workouts count karne ke liye (day-by-day loop, kyunke get_meals_by_user single-date filter leta hai)
    from sqlalchemy import func as sql_func

    from app.models.meal import Meal
    from app.models.workout import Workout

    meals_count_result= await db.execute(
        select(sql_func.count(Meal.id))
        .where(
            Meal.user_id == user_id,
            sql_func.date(Meal.logged_at) >= week_start,
            sql_func.date(Meal.logged_at) <= week_end,
        )
    )
    meals_count = meals_count_result.scalar_one()
    

    workouts_count_result= await db.execute(
            select(sql_func.count(Workout.id))
            .where(
                Workout.user_id == user_id,
                sql_func.date(Workout.logged_at) >= week_start,
                sql_func.date(Workout.logged_at) <= week_end,
            )
        )
    workouts_count = workouts_count_result.scalar_one()

    insight = await generate_weekly_coach_insight(week_start, week_end, daily_summary, meals_count, workouts_count, user)

    # Existing report check karo (agar dobara generate ho raha ho usi hafte ke liye)
    result = await db.execute(
        select(WeeklyReport).where(WeeklyReport.user_id == user_id,WeeklyReport.week_start == week_start)
    )
    report = result.scalar_one_or_none()

    if report:
        report.summary = insight.summary
        report.highlights = insight.highlights
        report.suggestions = insight.suggestions
    else:
        report = WeeklyReport(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            summary=insight.summary,
            highlights=insight.highlights,
            suggestions=insight.suggestions,
        )
        db.add(report)

    await db.commit()
    await db.refresh(report)
    return report


async def get_weekly_reports(db: AsyncSession, user_id: uuid.UUID) -> list[WeeklyReport]:
    result = await db.execute(
        select(WeeklyReport).where(WeeklyReport.user_id == user_id).order_by(WeeklyReport.week_start.desc())
    )
    return list(result.scalars().all())
