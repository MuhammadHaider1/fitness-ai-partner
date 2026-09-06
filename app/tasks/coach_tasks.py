import asyncio
import uuid
from datetime import date, timedelta

from app.core.dates import today_local

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.agents.coach_agent import generate_daily_coach_insight
from app.core.celery_app import celery_app
from app.core.config import settings
from app.models.user import User
from app.services.daily_log_service import get_daily_log, get_daily_log_summary
from app.services.meal_service import get_meals_by_user
from app.services.workout_service import get_workouts_by_user


async def _generate_coach_insight_for_user(user_id_str: str, log_date_str: str) -> dict:
    user_id = uuid.UUID(user_id_str)
    log_date = date.fromisoformat(log_date_str)

    worker_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    WorkerSession = async_sessionmaker(worker_engine, expire_on_commit=False)

    try:
        async with WorkerSession() as db:
            daily_log = await get_daily_log(db, user_id, log_date)
            await db.commit() 
            
            meals = await get_meals_by_user(db, user_id, log_date)
            workouts = await get_workouts_by_user(db, user_id, log_date)
            summary = await get_daily_log_summary(db, user_id, log_date - timedelta(days=30), log_date)

            insight = await generate_daily_coach_insight(daily_log, meals, workouts, summary.current_streak)

            return {
                "summary": insight.summary,
                "highlights": insight.highlights,
                "suggestions": insight.suggestions,
            }
    finally:
        await worker_engine.dispose()


# bind=True allows access to the self object to trigger manual retries
@celery_app.task(
    name="generate_coach_insight_task", 
    bind=True, 
    max_retries=5
)
def generate_coach_insight_task(self, user_id_str: str, log_date_str: str) -> dict:
    try:
        return asyncio.run(_generate_coach_insight_for_user(user_id_str, log_date_str))
    except Exception as exc:
        # Check if the error is due to a rate limit / quota exhaustion
        if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
            # Instructs Celery to wait 25 seconds before running this specific task again
            raise self.retry(exc=exc, countdown=25)
        raise exc


async def _generate_for_all_users(log_date_str: str) -> None:
    worker_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    WorkerSession = async_sessionmaker(worker_engine, expire_on_commit=False)
    
    try:
        async with WorkerSession() as db:
            result = await db.execute(select(User.id))
            user_ids = [str(uid) for uid in result.scalars().all()]
    finally:
        await worker_engine.dispose()

    for user_id_str in user_ids:
        generate_coach_insight_task.delay(user_id_str, log_date_str)


@celery_app.task(name="generate_daily_coach_for_all_users")
def generate_daily_coach_for_all_users() -> None:
    today_str = today_local().isoformat()  
    asyncio.run(_generate_for_all_users(today_str))
