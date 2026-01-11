"""
Schemas for recurring activities
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum
from .common import SportType, Difficulty, BaseResponse
from app.core.timezone import ensure_utc, is_future


class RecurringUpdateScope(str, Enum):
    """Scope of recurring activity update"""
    THIS_ONLY = "this_only"
    THIS_AND_FOLLOWING = "this_and_following"


class RecurringCancelScope(str, Enum):
    """Scope of recurring activity cancellation"""
    THIS_ONLY = "this_only"
    ENTIRE_SERIES = "entire_series"


class RecurringTemplateCreate(BaseModel):
    """Schema for creating recurring activity series"""
    title: str = Field(..., min_length=3, max_length=200, description="Activity title")
    description: Optional[str] = Field(None, max_length=2000)

    # Schedule settings
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week: 0=Monday, 6=Sunday")
    time_of_day: str = Field(..., pattern=r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', description="Time in HH:MM format")
    start_date: datetime = Field(..., description="First occurrence date")
    frequency: int = Field(4, ge=1, le=4, description="Times per month: 4=weekly, 2=bi-weekly, 1=monthly")
    total_occurrences: int = Field(..., ge=1, le=12, description="Total number of occurrences (max 12 = 3 months)")

    # Activity template
    location: str = Field(..., min_length=2, max_length=200, description="Meeting location")
    sport_type: SportType
    difficulty: Difficulty
    distance: Optional[float] = Field(None, ge=0, le=500, description="Distance in km")
    duration: Optional[int] = Field(None, ge=1, le=1440, description="Duration in minutes")
    max_participants: Optional[int] = Field(None, ge=1, le=1000)

    # Organization (one required)
    club_id: Optional[str] = Field(None, description="Club UUID")
    group_id: Optional[str] = Field(None, description="Group UUID")

    @field_validator('start_date')
    @classmethod
    def date_must_be_future(cls, v: datetime) -> datetime:
        """Start date must be in the future. Converts to UTC."""
        v_utc = ensure_utc(v)
        if not is_future(v_utc):
            raise ValueError('Start date must be in the future')
        return v_utc

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Субботняя пробежка",
                "description": "Еженедельная тренировка клуба",
                "day_of_week": 5,
                "time_of_day": "09:00",
                "start_date": "2025-01-04T09:00:00",
                "frequency": 4,
                "total_occurrences": 12,
                "location": "Центральный парк",
                "sport_type": "running",
                "difficulty": "medium",
                "distance": 10.0,
                "club_id": "abc123"
            }
        }
    )


class RecurringTemplateResponse(BaseResponse):
    """Schema for recurring template response"""
    title: str
    description: Optional[str]

    # Schedule
    day_of_week: int
    time_of_day: str
    frequency: int
    total_occurrences: int
    generated_count: int

    # Activity template
    location: Optional[str]
    sport_type: SportType
    difficulty: Difficulty
    distance: Optional[float]
    duration: Optional[int]
    max_participants: Optional[int]

    # Organization
    club_id: Optional[str]
    group_id: Optional[str]
    creator_id: str

    # Status
    active: bool

    # Computed
    club_name: Optional[str] = None
    group_name: Optional[str] = None


class RecurringSeriesCreateResponse(BaseModel):
    """Response after creating a recurring series"""
    template: RecurringTemplateResponse
    activities_created: int
    first_activity_id: str

    model_config = ConfigDict(from_attributes=True)


class RecurringUpdateRequest(BaseModel):
    """Request to update recurring activity"""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    location: Optional[str] = Field(None, min_length=2, max_length=200)
    difficulty: Optional[Difficulty] = None
    distance: Optional[float] = Field(None, ge=0, le=500)
    duration: Optional[int] = Field(None, ge=1, le=1440)
    max_participants: Optional[int] = Field(None, ge=1, le=1000)
    # Date can only be changed for THIS_ONLY scope
    date: Optional[datetime] = Field(None, description="New date/time (only for this_only scope)")


class RecurringActionResponse(BaseModel):
    """Response for recurring action (update/cancel)"""
    message: str
    affected_count: int
