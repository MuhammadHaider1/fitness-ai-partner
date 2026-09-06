import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.meal import MealCreate, MealRead, MealUpdate
from app.services.meal_service import (
    create_meal,
    delete_meal,
    get_meal_by_id,
    get_meals_by_user,
    update_meal,
)

router = APIRouter(prefix="/meals", tags=["meals"])

@router.post("/", response_model=MealRead, status_code=status.HTTP_201_CREATED)
async def log_meal(
    meal_in: MealCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meal = await create_meal(db, current_user.id, meal_in)
    return meal


@router.get("/", response_model=list[MealRead])
async def list_meals(
    log_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_meals_by_user(db, current_user.id, log_date)


@router.get("/{meal_id}", response_model=MealRead, status_code=status.HTTP_200_OK)
async def get_meal(
    meal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meal = await get_meal_by_id(db, meal_id, current_user.id)
    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found"
        )
    return meal


@router.patch("/{meal_id}", response_model=MealRead , status_code=status.HTTP_200_OK)
async def edit_meal(
    meal_id : uuid.UUID,
    update_in : MealUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    meal = await get_meal_by_id(db, meal_id, current_user.id)
    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found"
        )
    return await update_meal(db, meal , update_in)



@router.delete("/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_meal(
    meal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meal = await get_meal_by_id(db, meal_id, current_user.id)
    if not meal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meal not found"
        )
    await delete_meal(db, meal)
