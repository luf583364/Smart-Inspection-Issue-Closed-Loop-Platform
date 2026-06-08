from datetime import datetime, timedelta, timezone, tzinfo
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.core.config import settings


@lru_cache
def app_timezone() -> tzinfo:
    try:
        return ZoneInfo(settings.APP_TIMEZONE)
    except ZoneInfoNotFoundError:
        # China has no daylight-saving changes, so UTC+8 is a safe fallback
        # when the host/container lacks IANA timezone data.
        return timezone(timedelta(hours=8), name=settings.APP_TIMEZONE or "Asia/Shanghai")


def now_local() -> datetime:
    """Return naive local business time for DB fields displayed by the UI."""
    return datetime.now(app_timezone()).replace(tzinfo=None, microsecond=0)
