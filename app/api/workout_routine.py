from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.workout_routine import (
    WorkoutRoutineDayUpdate,
    WorkoutRoutineRead,
)
from app.services.workout_routine_service import (
    clear_routine_day,
    get_full_routine,
    get_routine_by_day,
    upsert_routine_day,
)

router = APIRouter(prefix="/workout-routine", tags=["workout-routine"])


@router.get("/", response_model=list[WorkoutRoutineRead])
async def get_routine(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_full_routine(db, current_user.id)


@router.get("/{day_of_week}", response_model=WorkoutRoutineRead)
async def get_day(
    day_of_week: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    routine = await get_routine_by_day(db, current_user.id, day_of_week)
    if not routine:
        raise HTTPException(status_code=404, detail="No routine saved for this day")
    return routine


@router.put("/{day_of_week}", response_model=WorkoutRoutineRead)
async def save_day(
    day_of_week: int,
    payload: WorkoutRoutineDayUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.day_of_week != day_of_week:
        raise HTTPException(status_code=400, detail="day_of_week in URL and body must match")
    if day_of_week < 0 or day_of_week > 6:
        raise HTTPException(status_code=400, detail="day_of_week must be 0 (Monday) to 6 (Sunday)")
    return await upsert_routine_day(db, current_user.id, payload)


@router.delete("/{day_of_week}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_day(
    day_of_week: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await clear_routine_day(db, current_user.id, day_of_week)