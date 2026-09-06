import uuid
from datetime import date

from sqlalchemy import func as sql_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dates import day_range
from app.models.daily_log import DailyLog
from app.models.meal import Meal
from app.schemas.daily_log import DailyLogSummary, DailyLogUpdate


async def get_or_create_daily_log(db: AsyncSession, user_id: uuid.UUID, log_date: date) -> DailyLog:
    stmt = select(DailyLog).where(DailyLog.user_id == user_id, DailyLog.log_date == log_date)
    result = await db.execute(stmt)
    daily_log = result.scalar_one_or_none()

    if daily_log is None:
        daily_log = DailyLog(user_id=user_id, log_date=log_date)
        db.add(daily_log)
        await db.commit()
        await db.refresh(daily_log)
    return daily_log


async def apply_meal_to_daily_log(db:AsyncSession ,
    user_id: uuid.UUID,
    log_date: date,
    calories: float,
    protein_g: float | None,
    carbs_g: float | None,
    fats_g: float | None,
    sign: int = 1,  # +1 jab meal add ho, -1 jab delete ho
) -> None:

    """Meal add/delete hone par DailyLog ke totals ko sync karo"""
    daily_log = await get_or_create_daily_log(db, user_id, log_date)

    daily_log.total_calories += sign * calories
    daily_log.total_protein_g += sign * (protein_g or 0)
    daily_log.total_carbs_g += sign * (carbs_g or 0)
    daily_log.total_fats_g += sign * (fats_g or 0)

    await db.commit()


async def update_daily_log(db:AsyncSession , user_id:uuid.UUID , log_date:date , update_in:DailyLogUpdate) -> DailyLog:
    daily_log = await get_or_create_daily_log(db, user_id , log_date)

    update_data = update_in.model_dump(exclude_unset=True)
    for feild, value in update_data.items():
        setattr(daily_log, feild, value) 

    await db.commit()
    await db.refresh(daily_log)
    return daily_log


async def get_daily_log(db:AsyncSession , user_id:uuid.UUID , log_date: date) -> DailyLog:
    return await get_or_create_daily_log(db,user_id,log_date)




async def recalculate_daily_log(db: AsyncSession, user_id: uuid.UUID, log_date: date) -> DailyLog:
    """DailyLog totals ko Meal table se dobara accurately calculate karo"""
    day_start, day_end = day_range(log_date)
    result = await db.execute(
        select(
            sql_func.coalesce(sql_func.sum(Meal.calories), 0),
            sql_func.coalesce(sql_func.sum(Meal.protein_g), 0),
            sql_func.coalesce(sql_func.sum(Meal.carbs_g), 0),
            sql_func.coalesce(sql_func.sum(Meal.fats_g), 0),
        ).where(
            Meal.user_id == user_id,
            Meal.logged_at >= day_start,
            Meal.logged_at < day_end,
        )
    )
    total_cal, total_protein, total_carbs, total_fats = result.one()

    daily_log = await get_or_create_daily_log(db, user_id, log_date)
    daily_log.total_calories = total_cal
    daily_log.total_protein_g = total_protein
    daily_log.total_carbs_g = total_carbs
    daily_log.total_fats_g = total_fats

    await db.commit()
    await db.refresh(daily_log)
    return daily_log



async def get_daily_log_history(
    db: AsyncSession, user_id: uuid.UUID, start_date: date, end_date: date
) -> list[DailyLog]:
    result = await db.execute(
        select(DailyLog)
        .where(
            DailyLog.user_id == user_id,
            DailyLog.log_date >= start_date,
            DailyLog.log_date <= end_date,
        )
        .order_by(DailyLog.log_date.asc())
    )
    return list(result.scalars().all())


async def get_daily_log_summary(db:AsyncSession , user_id:uuid.UUID,start_date: date , end_date:date) -> DailyLogSummary:
    logs = await get_daily_log_history(db , user_id,start_date,end_date)

    days_logged = len(logs)

    if days_logged == 0:
        return DailyLogSummary(
            start_date=start_date,
            end_date=end_date,
            days_logged=0,
            days_on_target=0,
            average_calories=0,
            average_protein_g=0,
            average_carbs_g=0,
            average_fats_g=0,
            current_streak=0,
        )

    days_on_target = sum(
    1 for log in logs
    if log.calorie_target is not None and log.total_calories <= log.calorie_target
)
    avg_calories = sum(log.total_calories for log in logs) / days_logged
    avg_protein = sum(log.total_protein_g for log in logs) / days_logged
    avg_carbs = sum(log.total_carbs_g for log in logs) / days_logged
    avg_fats = sum(log.total_fats_g for log in logs) / days_logged


    # Streak
    current_streak = 0
    for log in reversed(logs):
        if log.calorie_target is not None and log.total_calories <= log.calorie_target:
            current_streak += 1
        else:
            break

    return DailyLogSummary(
        start_date=start_date,
        end_date=end_date,
        days_logged=days_logged,
        days_on_target=days_on_target,
        average_calories=round(avg_calories, 1),
        average_protein_g=round(avg_protein, 1),
        average_carbs_g=round(avg_carbs, 1),
        average_fats_g=round(avg_fats, 1),
        current_streak=current_streak,
    )    


async def apply_workout_to_daily_log(
    db: AsyncSession,
    user_id: uuid.UUID,
    log_date: date,
    calories_burned: float,
    sign: int = 1,
) -> None:
    """Workout add/delete/update hone par DailyLog ke calories_burned ko sync karo"""
    daily_log = await get_or_create_daily_log(db, user_id, log_date)
    daily_log.total_calories_burned += sign * calories_burned
    await db.commit()