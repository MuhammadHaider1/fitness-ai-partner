import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workout_routine import WorkoutRoutine
from app.schemas.workout_routine import WorkoutRoutineDayUpdate


async def get_routine_by_day(db: AsyncSession, user_id: uuid.UUID, day_of_week: int) -> WorkoutRoutine | None:
    result = await db.execute(
        select(WorkoutRoutine).where(
            WorkoutRoutine.user_id == user_id,
            WorkoutRoutine.day_of_week == day_of_week,
        )
    )
    return result.scalar_one_or_none()


async def get_full_routine(db: AsyncSession, user_id: uuid.UUID) -> list[WorkoutRoutine]:
    result = await db.execute(
        select(WorkoutRoutine)
        .where(WorkoutRoutine.user_id == user_id)
        .order_by(WorkoutRoutine.day_of_week)
    )
    return list(result.scalars().all())


async def upsert_routine_day(db: AsyncSession, user_id: uuid.UUID, day_in: WorkoutRoutineDayUpdate) -> WorkoutRoutine:
    routine = await get_routine_by_day(db, user_id, day_in.day_of_week)
    exercises = [e.model_dump() for e in day_in.exercises]
    if routine is None:
        routine = WorkoutRoutine(user_id=user_id, day_of_week=day_in.day_of_week, exercises=exercises)
        db.add(routine)
    else:
        routine.exercises = exercises
    await db.commit()
    await db.refresh(routine)
    return routine


async def clear_routine_day(db: AsyncSession, user_id: uuid.UUID, day_of_week: int) -> None:
    routine = await get_routine_by_day(db, user_id, day_of_week)
    if routine:
        await db.delete(routine)
        await db.commit()