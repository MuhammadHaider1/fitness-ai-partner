import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class WeeklyReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    week_start: date
    week_end: date
    summary: str
    highlights: list[str]
    suggestions: list[str]
    created_at: datetime