"""
Timezone utilities for consistent datetime handling across the application.

All dates in the database are stored in UTC.
User-facing dates include timezone information for proper conversion.

Usage:
    from app.core.timezone import utc_now, ensure_utc, to_user_tz

    # Get current time in UTC
    now = utc_now()

    # Ensure a datetime is UTC-aware
    dt = ensure_utc(some_datetime)

    # Convert to user's timezone for display
    local_dt = to_user_tz(dt, "Europe/Moscow")
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import re

# Try to import ZoneInfo, fallback to fixed offset for Moscow if tzdata not available
try:
    from zoneinfo import ZoneInfo
    ZONEINFO_AVAILABLE = True
except ImportError:
    ZONEINFO_AVAILABLE = False
    ZoneInfo = None

# Default timezone for the app
DEFAULT_TIMEZONE = "Asia/Almaty"
# Almaty is UTC+5
DEFAULT_OFFSET = timezone(timedelta(hours=5))

# Country to timezone mapping
# Used when we don't have city-level timezone info
COUNTRY_TIMEZONES = {
    "Kazakhstan": "Asia/Almaty",      # UTC+5 (whole country)
    "Russia": "Europe/Moscow",         # UTC+3 (default, varies by region)
    "Uzbekistan": "Asia/Tashkent",     # UTC+5
    "Kyrgyzstan": "Asia/Bishkek",      # UTC+6
    "UAE": "Asia/Dubai",               # UTC+4
    "United Arab Emirates": "Asia/Dubai",
}

# Fallback timezone offsets when ZoneInfo is not available
TIMEZONE_OFFSETS = {
    "Asia/Almaty": timezone(timedelta(hours=5)),
    "Europe/Moscow": timezone(timedelta(hours=3)),
    "Asia/Tashkent": timezone(timedelta(hours=5)),
    "Asia/Bishkek": timezone(timedelta(hours=6)),
    "Asia/Dubai": timezone(timedelta(hours=4)),
}

# Russian month names for date formatting
RUSSIAN_MONTHS = {
    "January": "января",
    "February": "февраля",
    "March": "марта",
    "April": "апреля",
    "May": "мая",
    "June": "июня",
    "July": "июля",
    "August": "августа",
    "September": "сентября",
    "October": "октября",
    "November": "ноября",
    "December": "декабря",
}

# Russian day of week names (abbreviated)
RUSSIAN_WEEKDAYS = {
    "Mon": "Пн",
    "Tue": "Вт",
    "Wed": "Ср",
    "Thu": "Чт",
    "Fri": "Пт",
    "Sat": "Сб",
    "Sun": "Вс",
}


def _to_russian(text: str) -> str:
    """Convert English month and weekday names to Russian."""
    result = text
    for eng, rus in RUSSIAN_MONTHS.items():
        result = result.replace(eng, rus)
    for eng, rus in RUSSIAN_WEEKDAYS.items():
        result = result.replace(eng, rus)
    return result


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    Always use this instead of datetime.now() or datetime.utcnow().
    """
    return datetime.now(timezone.utc)


def _get_timezone(tz_name: str):
    """Get timezone object, with fallback for when tzdata is not available."""
    if ZONEINFO_AVAILABLE:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            pass
    # Fallback to known offsets or default
    return TIMEZONE_OFFSETS.get(tz_name, DEFAULT_OFFSET)


def get_timezone_for_location(country: str = None, city: str = None) -> str:
    """
    Get timezone string for a given location.

    Args:
        country: Country name (e.g., "Kazakhstan")
        city: City name (optional, for future city-level mapping)

    Returns:
        IANA timezone string (e.g., "Asia/Almaty")
    """
    # For now, use country-level mapping
    # In future, can add city-level mapping for countries with multiple timezones
    if country and country in COUNTRY_TIMEZONES:
        return COUNTRY_TIMEZONES[country]
    return DEFAULT_TIMEZONE


def to_local_time(dt: datetime, country: str = None, city: str = None) -> datetime:
    """
    Convert UTC datetime to local time based on location.

    Args:
        dt: UTC datetime (naive or aware)
        country: Country name for timezone lookup
        city: City name (optional, for future use)

    Returns:
        Datetime in local timezone
    """
    if dt is None:
        return None

    # Ensure dt is UTC-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Get timezone for location
    tz_name = get_timezone_for_location(country, city)
    local_tz = _get_timezone(tz_name)

    return dt.astimezone(local_tz)


def format_datetime_local(
    dt: datetime,
    country: str = None,
    city: str = None,
    fmt: str = "%d %B в %H:%M"
) -> str:
    """
    Format UTC datetime to local time string for display in bot messages.

    Args:
        dt: UTC datetime
        country: Country name for timezone lookup
        city: City name (optional)
        fmt: strftime format string

    Returns:
        Formatted datetime string in local time (with Russian month/weekday names)
    """
    local_dt = to_local_time(dt, country, city)
    if local_dt is None:
        return ""
    formatted = local_dt.strftime(fmt)
    return _to_russian(formatted)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensure a datetime is UTC-aware.

    - If None, returns None
    - If naive (no timezone), assumes it's in DEFAULT_TIMEZONE and converts to UTC
    - If already has timezone, converts to UTC

    This handles the case where frontend sends naive datetimes
    that are actually in user's local time.

    WARNING: Do NOT use this for datetimes from database!
    Database stores naive UTC datetimes - use ensure_utc_from_db() instead.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Naive datetime - assume it's in default timezone
        local_tz = _get_timezone(DEFAULT_TIMEZONE)
        dt = dt.replace(tzinfo=local_tz)

    # Convert to UTC
    return dt.astimezone(timezone.utc)


def ensure_utc_from_db(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensure a datetime from database is UTC-aware.

    - If None, returns None
    - If naive (no timezone), assumes it's already UTC (as stored in DB)
    - If already has timezone, converts to UTC

    Use this for datetimes read from database, which are stored as naive UTC.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Naive datetime from DB - it's already UTC, just add tzinfo
        return dt.replace(tzinfo=timezone.utc)

    # Already has timezone, convert to UTC
    return dt.astimezone(timezone.utc)


def ensure_utc_or_now(dt: Optional[datetime]) -> datetime:
    """
    Ensure a datetime is UTC-aware, or return current UTC time if None.
    """
    if dt is None:
        return utc_now()
    return ensure_utc(dt)


def to_user_tz(dt: datetime, tz_name: str = DEFAULT_TIMEZONE) -> datetime:
    """
    Convert a UTC datetime to user's timezone.

    Args:
        dt: UTC datetime (should be timezone-aware)
        tz_name: IANA timezone name (e.g., "Europe/Moscow", "Asia/Dubai")

    Returns:
        Datetime in user's timezone
    """
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        dt = dt.replace(tzinfo=timezone.utc)

    user_tz = _get_timezone(tz_name)
    return dt.astimezone(user_tz)


def parse_frontend_datetime(dt_str: str, user_tz: str = DEFAULT_TIMEZONE) -> datetime:
    """
    Parse a datetime string from frontend and convert to UTC.

    Frontend typically sends: "2025-01-15T07:00:00" (no timezone)
    This is interpreted as user's local time and converted to UTC.

    Args:
        dt_str: ISO format datetime string (may or may not have timezone)
        user_tz: User's timezone if not specified in string

    Returns:
        UTC timezone-aware datetime
    """
    # Try parsing with timezone info first
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is not None:
            # Already has timezone, convert to UTC
            return dt.astimezone(timezone.utc)
    except ValueError:
        pass

    # Parse as naive and assume user's timezone
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        local_tz = _get_timezone(user_tz)
        dt = dt.replace(tzinfo=local_tz)
        return dt.astimezone(timezone.utc)

    return dt.astimezone(timezone.utc)


def format_for_frontend(dt: datetime, user_tz: str = DEFAULT_TIMEZONE) -> str:
    """
    Format a UTC datetime for frontend display.

    Returns ISO format string in user's timezone.
    """
    local_dt = to_user_tz(dt, user_tz)
    return local_dt.isoformat()


def is_past(dt: datetime) -> bool:
    """
    Check if a datetime is in the past.

    Assumes naive datetime is UTC (as stored in database).
    Use this for Activity.date and other DB datetimes.
    """
    dt_utc = ensure_utc_from_db(dt)
    return dt_utc < utc_now()


def is_future(dt: datetime) -> bool:
    """
    Check if a datetime is in the future.

    Assumes naive datetime is UTC (as stored in database).
    Use this for Activity.date and other DB datetimes.
    """
    dt_utc = ensure_utc_from_db(dt)
    return dt_utc > utc_now()


# For backwards compatibility with existing code using datetime.utcnow()
# These can be used as default values in SQLAlchemy models
def utc_now_naive() -> datetime:
    """
    Get current UTC time as naive datetime (for DB storage compatibility).

    Use this for SQLAlchemy default values until we migrate to timezone-aware columns.
    """
    return datetime.utcnow()
