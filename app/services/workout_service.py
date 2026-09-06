import uuid

from sqlalchemy import func as sql_func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import Workout
from app.schemas.workout import WorkoutCreate, WorkoutUpdate
from app.services.daily_log_service import apply_workout_to_daily_log


async def create_workout(db: AsyncSession, user_id: uuid.UUID, workout_in: WorkoutCreate, source: str = "manual") -> AsyncSession:
    workout = Workout(
        user_id=user_id,
        workout_type=workout_in.workout_type,
        name=workout_in.name,
        duration_minutes=workout_in.duration_minutes,
        distance_km=workout_in.distance_km,
        sets=workout_in.sets,
        reps=workout_in.reps,
        weight_kg=workout_in.weight_kg,
        intensity=workout_in.intensity,
        calories_burned=workout_in.calories_burned,
        source=source,
    )

    db.add(workout)
    await db.commit()
    await db.refresh(workout)

    log_date = workout.logged_at.date()
    await apply_workout_to_daily_log(db, user_id, log_date, workout.calories_burned, sign=1)
    return workout


async def get_workouts_by_user(db:AsyncSession , user_id:uuid.UUID , log_date = None) -> list[Workout]:
    query = select(Workout).where(Workout.user_id == user_id)
    if log_date is not None:
        query = query.where(sql_func.date(Workout.logged_at) == log_date)

    query = query.order_by(Workout.logged_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_workout_by_id(db: AsyncSession, workout_id: uuid.UUID, user_id: uuid.UUID) -> Workout | None:
    result = await db.execute(
        select(Workout).where(Workout.id == workout_id, Workout.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_workout(db: AsyncSession, workout: Workout, update_in: WorkoutUpdate) -> Workout:
    log_date = workout.logged_at.date()
    user_id = workout.user_id 
    old_calories_burned = workout.calories_burned

    update_data = update_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workout, field, value)

    await db.commit()
    await db.refresh(workout)

    await apply_workout_to_daily_log(db, user_id, log_date, old_calories_burned, sign=-1)
    await apply_workout_to_daily_log(db, user_id, log_date, workout.calories_burned, sign=1)

    return workout


async def delete_workout(db: AsyncSession, workout: Workout) -> None:
    log_date = workout.logged_at.date()
    user_id = workout.user_id
    calories_burned = workout.calories_burned

    await db.delete(workout)
    await db.commit()

    await apply_workout_to_daily_log(db, user_id, log_date, calories_burned, sign=-1)