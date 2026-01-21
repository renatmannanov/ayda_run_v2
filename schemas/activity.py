from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer, ValidationInfo
from datetime import datetime
from typing import Optional, List
from .common import SportType, Difficulty, BaseResponse, ActivityVisibility, ActivityStatus, ParticipationStatus, serialize_datetime_utc
from app.core.timezone import ensure_utc, utc_now

class ActivityCreate(BaseModel):
    """Schema for creating activity"""
    title: str = Field(..., min_length=3, max_length=200, description="Activity title")
    description: Optional[str] = Field(None, max_length=2000)
    date: datetime = Field(..., description="Activity date and time")
    location: str = Field(..., min_length=2, max_length=200)

    # Location (both optional - will use user's location if not provided)
    city: Optional[str] = Field(None, min_length=2, max_length=100, description="City (optional, uses user's city if not provided)")
    country: Optional[str] = Field(None, max_length=100, description="Country (optional, defaults to Kazakhstan)")

    sport_type: SportType
    difficulty: Difficulty
    distance: Optional[float] = Field(None, ge=0, le=500, description="Distance in km")
    duration: Optional[int] = Field(None, ge=1, le=1440, description="Duration in minutes")
    max_participants: Optional[int] = Field(None, ge=1, le=1000)
    visibility: ActivityVisibility = ActivityVisibility.INVITE_ONLY
    is_open: bool = Field(default=True, description="True = anyone can join, False = join by request")
    club_id: Optional[int | str] = None  # UUID (temporarily accepts int from frontend bug)
    group_id: Optional[int | str] = None  # UUID (temporarily accepts int from frontend bug)

    @field_validator('club_id', 'group_id', mode='before')
    @classmethod
    def convert_id_to_string(cls, v: Optional[int | str]) -> Optional[str]:
        """Convert integer ID to string (temporary workaround for frontend bug)"""
        if v is None:
            return None
        if isinstance(v, int):
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️ FRONTEND BUG: Received integer ID {v} instead of UUID string. Converting to '{v}' but this will likely cause 'not found' error.")
            return str(v)
        return v

    @field_validator('date')
    @classmethod
    def date_must_be_future(cls, v: datetime) -> datetime:
        """Activity date must be in the future. Converts to UTC."""
        v_utc = ensure_utc(v)
        if v_utc <= utc_now():
            raise ValueError('Activity date must be in the future')
        return v_utc

    @field_validator('location', 'title', 'description', mode='before')
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Strip leading/trailing whitespace from text fields."""
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip()
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Утренняя пробежка",
                "description": "Легкая пробежка в парке",
                "date": "2025-12-20T07:00:00",
                "location": "Центральный парк",
                "sport_type": "running",
                "difficulty": "easy",
                "distance": 5.0,
                "duration": 30,
                "max_participants": 10
            }
        }
    )

class ActivityUpdate(BaseModel):
    """Schema for updating activity.

    Note: sport_type, club_id, group_id are immutable after creation.
    """
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    date: Optional[datetime] = None
    location: Optional[str] = Field(None, min_length=2, max_length=200)
    # sport_type is immutable - cannot be changed after creation
    difficulty: Optional[Difficulty] = None
    distance: Optional[float] = Field(None, ge=0, le=500)
    duration: Optional[int] = Field(None, ge=1, le=1440)
    max_participants: Optional[int] = Field(None, ge=1, le=1000)
    visibility: Optional[ActivityVisibility] = None
    is_open: Optional[bool] = None
    status: Optional[ActivityStatus] = None

    @field_validator('date')
    @classmethod
    def date_must_be_future(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Activity date must be in the future. Converts to UTC."""
        if v is None:
            return None
        v_utc = ensure_utc(v)
        if v_utc <= utc_now():
            raise ValueError('Activity date must be in the future')
        return v_utc

    @field_validator('location', 'title', 'description', mode='before')
    @classmethod
    def strip_whitespace(cls, v: Optional[str]) -> Optional[str]:
        """Strip leading/trailing whitespace from text fields."""
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip()
        return v

class ActivityResponse(BaseResponse):
    """Schema for activity response"""
    title: str
    description: Optional[str]
    date: datetime
    location: Optional[str]

    @field_serializer('date')
    def serialize_date(self, dt: datetime) -> str:
        return serialize_datetime_utc(dt)

    # Location
    country: str
    city: str

    sport_type: SportType
    difficulty: Difficulty
    distance: Optional[float]
    duration: Optional[int]
    max_participants: Optional[int]
    visibility: ActivityVisibility
    is_open: bool
    status: ActivityStatus
    club_id: Optional[str]  # UUID
    group_id: Optional[str]  # UUID
    creator_id: str  # UUID

    # GPX file
    gpx_file_id: Optional[str] = None
    gpx_filename: Optional[str] = None
    has_gpx: bool = False

    # Computed fields
    participants_count: int = 0
    is_joined: bool = False
    is_creator: bool = False
    participation_status: Optional[ParticipationStatus] = None  # User's participation status (awaiting, attended, missed, etc.)
    can_view_participants: bool = True  # False if closed and not member
    can_download_gpx: bool = True  # False if closed and not member
    club_name: Optional[str] = None
    group_name: Optional[str] = None
    creator_name: Optional[str] = None  # Creator's display name

    # Organizer permissions (for club/group activities)
    is_club_admin: bool = False
    is_group_admin: bool = False
    can_mark_attendance: bool = False  # True if past + club/group activity + is organizer

    # Recurring activity info
    recurring_template_id: Optional[str] = None
    recurring_sequence: Optional[int] = None  # Position in series (1, 2, 3...)
    is_recurring: bool = False  # True if part of recurring series


# ============================================================================
# Attendance Marking (for organizers)
# ============================================================================

class AttendanceItem(BaseModel):
    """Single attendance mark for a participant"""
    user_id: str  # UUID
    attended: Optional[bool] = None  # True = attended, False = missed, None = not marked


class MarkAttendanceRequest(BaseModel):
    """Request to mark attendance for multiple participants"""
    participants: List[AttendanceItem]


class AddParticipantRequest(BaseModel):
    """Request to add a club/group member as participant"""
    user_id: str  # UUID
    attended: bool = True  # Mark as attended by default when manually adding
