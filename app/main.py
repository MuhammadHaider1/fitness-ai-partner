from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.coach_agent import router as coach_agent_router
from app.api.daily_log import router as daily_log_router
from app.api.entry_agent import router as entry_agent_router
from app.api.meal import router as meal_router
from app.api.meal_agent import router as meal_agent_router
from app.api.target_agent import router as target_agent_router
from app.api.weekly_report import router as weekly_report_router
from app.api.workout import router as workouts_router
from app.api.workout_agent import router as workout_agent_router

app = FastAPI(title="Fitness AI Partner")

app.include_router(auth_router)
app.include_router(meal_router)
app.include_router(daily_log_router)
app.include_router(meal_agent_router)
app.include_router(workouts_router)
app.include_router(workout_agent_router)
app.include_router(entry_agent_router)
app.include_router(coach_agent_router)
app.include_router(weekly_report_router)
app.include_router(target_agent_router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Fitness AI Partner API!"}
