from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.weekly_report import WeeklyReportRead
from app.services.weekly_report_service import (
    generate_and_save_weekly_report,
    get_weekly_reports,
)

router = APIRouter(prefix="/weekly-report", tags=["weekly-report"])


@router.post("/generate", response_model=WeeklyReportRead , status_code=status.HTTP_201_CREATED)
async def generate_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # is hafte ka Monday
    week_end = week_start + timedelta(days=6)
    try:
        return await generate_and_save_weekly_report(db, current_user.id, week_start, week_end)
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI is busy right now (Gemini rate limit reached). Please try again in a minute.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Weekly report could not be generated. Please try again.",
        )


@router.get("/", response_model=list[WeeklyReportRead],status_code=status.HTTP_200_OK)
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_weekly_reports(db, current_user.id)