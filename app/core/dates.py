from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Karachi")


def local_date(dt: datetime) -> date:
    """Timestamp ko Asia/Karachi ke calendar date mein bucketing karo."""
    return dt.astimezone(TZ).date()


def today_local() -> date:
    return datetime.now(TZ).date()


def day_range(log_date: date) -> tuple[datetime, datetime]:
    """PKT day ki [start, end) boundaries — DB range-filtering ke liye."""
    start = datetime.combine(log_date, time.min, tzinfo=TZ)
    return start, start + timedelta(days=1)