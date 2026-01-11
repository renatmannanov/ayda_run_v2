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

# Try to import ZoneInfo, fallback to fixed offset for Moscow if tzdata not available
try:
    from zoneinfo import ZoneInfo
    ZONEINFO_AVAILABLE = True
except ImportError:
    ZONEINFO_AVAILABLE = False
    ZoneInfo = None

# Default timezone for the app (Moscow for now, will be user-configurable)
DEFAULT_TIMEZONE = "Europe/Moscow"
# Moscow is UTC+3
DEFAULT_OFFSET = timezone(timedelta(hours=3))


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
    # Fallback to default offset (Moscow UTC+3)
    return DEFAULT_OFFSET


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensure a datetime is UTC-aware.

    - If None, returns None
    - If naive (no timezone), assumes it's in DEFAULT_TIMEZONE and converts to UTC
    - If already has timezone, converts to UTC

    This handles the case where frontend sends naive datetimes
    that are actually in user's local time.
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Naive datetime - assume it's in default timezone
        local_tz = _get_timezone(DEFAULT_TIMEZONE)
        dt = dt.replace(tzinfo=local_tz)

    # Convert to UTC
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

    Handles both naive and aware datetimes.
    """
    dt_utc = ensure_utc(dt)
    return dt_utc < utc_now()


def is_future(dt: datetime) -> bool:
    """
    Check if a datetime is in the future.

    Handles both naive and aware datetimes.
    """
    dt_utc = ensure_utc(dt)
    return dt_utc > utc_now()


# For backwards compatibility with existing code using datetime.utcnow()
# These can be used as default values in SQLAlchemy models
def utc_now_naive() -> datetime:
    """
    Get current UTC time as naive datetime (for DB storage compatibility).

    Use this for SQLAlchemy default values until we migrate to timezone-aware columns.
    """
    return datetime.utcnow()
