import asyncio
import uuid
from datetime import date, timedelta

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.services.weekly_report_service import generate_and_save_weekly_report


async def _generate_weekly_report_for_user(user_id_str: str, week_start_str: str, week_end_str: str) -> dict:
    user_id = uuid.UUID(user_id_str)
    week_start = date.fromisoformat(week_start_str)
    week_end = date.fromisoformat(week_end_str)

    async with AsyncSessionLocal() as db:
        report = await generate_and_save_weekly_report(db, user_id, week_start, week_end)
        return {"summary": report.summary, "highlights": report.highlights, "suggestions": report.suggestions}


@celery_app.task(name="generate_weekly_report_task")
def generate_weekly_report_task(user_id_str: str, week_start_str: str, week_end_str: str) -> dict:
    return asyncio.run(_generate_weekly_report_for_user(user_id_str, week_start_str, week_end_str))


async def _generate_for_all_users_weekly() -> None:
    today = date.today()
    week_start = today - timedelta(days=today.weekday() + 7)  # pichla poora hafta
    week_end = week_start + timedelta(days=6)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User.id))
        user_ids = [str(uid) for uid in result.scalars().all()]

    for user_id_str in user_ids:
        generate_weekly_report_task.delay(user_id_str, week_start.isoformat(), week_end.isoformat())


@celery_app.task(name="generate_weekly_reports_for_all_users")
def generate_weekly_reports_for_all_users() -> None:
    asyncio.run(_generate_for_all_users_weekly())