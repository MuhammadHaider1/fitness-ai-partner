from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.daily_log import DailyLogRead, DailyLogSummary, DailyLogUpdate
from app.services.daily_log_service import (
    get_daily_log,
    get_daily_log_history,
    get_daily_log_summary,
    recalculate_daily_log,
    update_daily_log,
)

router = APIRouter(prefix="/daily-log" , tags=["daily-log"])

@router.get("/history", response_model=list[DailyLogRead])
async def get_history(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date",
        )
    return await get_daily_log_history(db, current_user.id, start_date, end_date)

@router.get("/" , response_model=DailyLogRead , status_code=status.HTTP_200_OK)
async def get_today_or_date_log(
    log_date: date = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_daily_log(db , current_user.id , log_date)


@router.patch("/", response_model=DailyLogRead , status_code=status.HTTP_200_OK)
async def update_log(
    update_in: DailyLogUpdate,
    log_date: date = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await update_daily_log(db, current_user.id, log_date, update_in)


@router.post("/recalculate", response_model=DailyLogRead , status_code=status.HTTP_200_OK)
async def recalculate_log(
    log_date: date = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await recalculate_daily_log(db, current_user.id, log_date)


@router.get("/summary",response_model=DailyLogSummary , status_code=status.HTTP_200_OK)
async def get_log_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date",
        )
    return await get_daily_log_summary(db , current_user.id , start_date , end_date)
