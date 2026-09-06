from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "fitness-ai-partner",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.coach_tasks","app.tasks.weekly_report_tasks"],
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Karachi",
    enable_utc=True,
)


celery_app.conf.beat_schedule = {
    "daily-coach-every-night": {
        "task": "generate_daily_coach_for_all_users",
        "schedule": crontab(hour=23, minute=0),  # Raat 11 baje
    },
    "weekly-report-every-monday": {
        "task": "generate_weekly_reports_for_all_users",
        "schedule": crontab(hour=6, minute=0, day_of_week=1),  # Monday subah 6 baje
    },
}