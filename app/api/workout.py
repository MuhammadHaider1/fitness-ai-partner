import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.workout import WorkoutCreate, WorkoutRead, WorkoutUpdate
from app.services.workout_service import (
    create_workout,
    delete_workout,
    get_workout_by_id,
    get_workouts_by_user,
    update_workout,
)

router = APIRouter(prefix="/workouts", tags=["workouts"])

@router.post("/", response_model=WorkoutRead, status_code=status.HTTP_201_CREATED)
async def log_workout(
    workout_in: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_workout(db, current_user.id, workout_in)


@router.get("/", response_model=list[WorkoutRead])
async def list_workouts(
    log_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_workouts_by_user(db, current_user.id, log_date)


@router.patch("/{workout_id}", response_model=WorkoutRead)
async def edit_workout(
    workout_id: uuid.UUID,
    update_in: WorkoutUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workout = await get_workout_by_id(db, workout_id, current_user.id)
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    return await update_workout(db, workout, update_in)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_workout(
    workout_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workout = await get_workout_by_id(db, workout_id, current_user.id)
    if not workout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
    await delete_workout(db, workout)
