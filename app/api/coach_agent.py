from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.coach_agent import chat_with_coach, generate_daily_coach_insight
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.coach import CoachAskRequest, CoachAskResponse, DailyCoachResponse
from app.services.daily_log_service import get_daily_log, get_daily_log_summary
from app.services.meal_service import get_meals_by_user
from app.services.workout_service import get_workouts_by_user

router = APIRouter(prefix="/coach", tags=["coach"])


@router.get("/daily", response_model=DailyCoachResponse)
async def get_daily_coach_feedback(
    log_date: date = Query(default_factory=date.today),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    daily_log = await get_daily_log(db, current_user.id, log_date)
    meals = await get_meals_by_user(db, current_user.id, log_date)
    workouts = await get_workouts_by_user(db, current_user.id, log_date)

    # Current streak nikalne ke liye pichle 30 din ka summary use karte hain
    summary = await get_daily_log_summary(db, current_user.id, log_date - timedelta(days=30), log_date)

    try:
        insight = await generate_daily_coach_insight(daily_log, meals, workouts, summary.current_streak, current_user)
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI coach is busy right now (Gemini rate limit reached). Please try again in a minute.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI coach could not generate insight. Please try again.",
        )

    return DailyCoachResponse(
        log_date=log_date,
        summary=insight.summary,
        highlights=insight.highlights,
        suggestions=insight.suggestions,
    )


@router.post("/ask", response_model=CoachAskResponse)
async def ask_coach(
    payload: CoachAskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    end = date.today()
    context_rows: list[str] = []
    for offset in range(7):
        d = end - timedelta(days=offset)
        log = await get_daily_log(db, current_user.id, d)
        if log is not None:
            context_rows.append(
                f"- {d}: {log.total_calories} kcal, protein {log.total_protein_g}g, "
                f"carbs {log.total_carbs_g}g, fats {log.total_fats_g}g, target {log.calorie_target} kcal"
            )

    try:
        reply = await chat_with_coach(current_user, payload.message, context_rows)
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="AI coach is busy right now (rate limit reached). Please try again in a minute.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI coach could not answer right now. Please try again.",
        )

    return CoachAskResponse(reply=reply)