from datetime import date

from pydantic import BaseModel, Field


class DailyCoachResponse(BaseModel):
    log_date: date
    summary: str
    highlights: list[str]
    suggestions: list[str]


class CoachAskRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class CoachAskResponse(BaseModel):
    reply: str