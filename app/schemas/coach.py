from datetime import date

from pydantic import BaseModel


class DailyCoachResponse(BaseModel):
    log_date: date
    summary: str
    highlights: list[str]
    suggestions: list[str]