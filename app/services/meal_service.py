import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meal import Meal
from app.schemas.meal import MealCreate, MealUpdate
from app.services.daily_log_service import apply_meal_to_daily_log


async def create_meal(db: AsyncSession, user_id: uuid.UUID, meal_in: MealCreate , source: str = "manual") -> Meal:
    meal = Meal(
        user_id=user_id,
        food_name=meal_in.food_name,
        meal_type=meal_in.meal_type,
        calories=meal_in.calories,
        protein_g=meal_in.protein_g,
        carbs_g=meal_in.carbs_g,
        fats_g=meal_in.fats_g,
        source=source,
    )
    db.add(meal)
    await db.commit()
    await db.refresh(meal)

    log_date= meal.logged_at.date()
    await apply_meal_to_daily_log(
        db, user_id , log_date,
        calories=meal.calories,
        protein_g=meal.protein_g,
        carbs_g=meal.carbs_g,
        fats_g=meal.fats_g,
        sign=1,
        )

    return meal


async def get_meals_by_user(db: AsyncSession, user_id: uuid.UUID, log_date=None) -> list[Meal]:
    query = select(Meal).where(Meal.user_id == user_id)
    if log_date is not None:
        from sqlalchemy import func as sql_func
        query = query.where(sql_func.date(Meal.logged_at) == log_date)
    query = query.order_by(Meal.logged_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())

async def get_meal_by_id(db: AsyncSession, meal_id: uuid.UUID , user_id: uuid.UUID) -> Meal | None:
    result = await db.execute(select(Meal).where(Meal.id == meal_id, Meal.user_id == user_id))
    return result.scalar_one_or_none()

async def delete_meal(db: AsyncSession, meal: Meal) -> None:
    log_date = meal.logged_at.date()
    user_id = meal.user_id
    calories, protein_g, carbs_g, fats_g = meal.calories, meal.protein_g, meal.carbs_g, meal.fats_g

    await db.delete(meal)
    await db.commit()

    await apply_meal_to_daily_log(
        db, user_id, log_date,
        calories=calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fats_g=fats_g,
        sign=-1,
    )

async def update_meal(db:AsyncSession , meal: Meal , update_in: MealUpdate) -> Meal:
    log_date = meal.logged_at.date()
    user_id = meal.user_id

    # Save old values for subtraction process
    old_calories = meal.calories
    old_protien_g = meal.protein_g
    old_carbs_g = meal.carbs_g
    old_fats_g = meal.fats_g

    # Applying New Feilds 
    update_data = update_in.model_dump(exclude_unset=True)
    for feild , value in update_data.items():
        setattr(meal,feild,value)

    
    # Step 1: Remove Old values from daily log
    await apply_meal_to_daily_log(
        db,user_id,log_date,
        calories=old_calories,
        protein_g=old_protien_g,
        carbs_g=old_carbs_g,
        fats_g=old_fats_g,
        sign=-1
    )

    #Step 2: Adding Updating values to daily_log
    await apply_meal_to_daily_log(
        db, user_id, log_date,
        calories=meal.calories,
        protein_g=meal.protein_g,
        carbs_g=meal.carbs_g,
        fats_g=meal.fats_g,
        sign=1,
    )

    await db.commit()
    await db.refresh(meal)
    

    return meal