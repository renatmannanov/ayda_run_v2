import json
from pydantic import BaseModel, field_serializer, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from .common import ParticipationStatus, serialize_datetime_utc

class UserResponse(BaseModel):
    """Response model for user"""
    model_config = ConfigDict(from_attributes=True)

    id: str  # UUID
    telegram_id: int | str  # Accept int from DB, serialize to string for JSON
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]

    @field_serializer('telegram_id', when_used='always')
    def serialize_telegram_id(self, telegram_id: int | str) -> str:
        """Convert telegram_id to string for JSON safety"""
        return str(telegram_id)

    # Location
    country: str
    city: str

    # Profile
    photo: Optional[str] = None  # Telegram avatar file_id
    strava_link: Optional[str] = None  # URL to Strava profile
    is_premium: bool = False
    show_photo: bool = True  # Show photo instead of initials

    # Onboarding
    has_completed_onboarding: bool
    preferred_sports: Optional[str]  # JSON string

    # Activity tracking
    first_seen_at: datetime
    last_seen_at: datetime

    # Timestamps
    created_at: datetime

    @field_serializer('first_seen_at', 'last_seen_at', 'created_at')
    def serialize_datetimes(self, dt: datetime) -> str:
        return serialize_datetime_utc(dt)

class UserProfileUpdate(BaseModel):
    """Request model for updating user profile"""
    photo: Optional[str] = None  # Telegram file_id or URL
    strava_link: Optional[str] = None  # URL to Strava profile
    show_photo: Optional[bool] = None  # Show photo instead of initials

class UserStatsResponse(BaseModel):
    """Response model for user statistics"""
    total_activities: int  # Total activities joined
    completed_activities: int  # Activities attended
    total_distance: float  # Sum of distances
    most_frequent_sport: Optional[str]  # Most frequent sport type
    attendance_rate: int  # Percentage of completed activities

class ParticipantResponse(BaseModel):
    """Response model for participant"""
    model_config = ConfigDict(from_attributes=True)

    user_id: str  # UUID
    telegram_id: int | str  # Accept int from DB, serialize to string for JSON
    username: Optional[str]
    first_name: Optional[str]
    name: str  # Display name for frontend
    status: ParticipationStatus
    attended: Optional[bool] = None  # True = attended, False = missed, None = not marked
    registered_at: datetime
    preferred_sports: Optional[str] = None  # JSON string of sport preferences

    @field_serializer('registered_at')
    def serialize_registered_at(self, dt: datetime) -> str:
        return serialize_datetime_utc(dt)
    photo: Optional[str] = None  # Telegram avatar file_id or URL
    strava_link: Optional[str] = None  # URL to Strava profile
    show_photo: bool = False  # Show photo instead of initials
    is_organizer: bool = False  # True if creator of the activity

    # Training link data (post-training flow)
    training_link: Optional[str] = None  # URL to Strava/Garmin/etc
    training_link_source: Optional[str] = None  # "manual" | "strava_auto"
    strava_activity_data: Optional[dict] = None  # Parsed JSON with distance, time, etc.

    @field_validator('strava_activity_data', mode='before')
    @classmethod
    def parse_strava_data(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_serializer('telegram_id', when_used='always')
    def serialize_telegram_id(self, telegram_id: int | str) -> str:
        """Convert telegram_id to string for JSON safety"""
        return str(telegram_id)


# ============================================================================
# Detailed Statistics Schemas
# ============================================================================

class ClubStats(BaseModel):
    """Statistics per club/group"""
    id: str
    name: str
    avatar: Optional[str] = None  # emoji or file_id
    initials: Optional[str] = None
    type: str  # 'club' or 'group'
    registered: int
    attended: int


class SportStats(BaseModel):
    """Statistics per sport type"""
    id: str  # 'running', 'trail', etc.
    icon: str  # emoji
    name: str  # 'Бег', 'Трейл', etc.
    count: int


class UserDetailedStatsResponse(BaseModel):
    """Detailed user statistics response"""
    period: str  # 'month', 'quarter', 'year', 'all'
    registered: int  # Total registered activities
    attended: int  # Total attended activities
    attendance_rate: int  # Percentage
    clubs: List[ClubStats]  # Stats by club/group
    sports: List[SportStats]  # Stats by sport type


# ============================================================================
# Entity Counts (for creation limits)
# ============================================================================

class EntityCount(BaseModel):
    """Count info for a single entity type"""
    current: int
    max: int


class UserCountsResponse(BaseModel):
    """Response with user's entity counts and limits"""
    clubs: EntityCount
    groups: EntityCount
    activities_upcoming: EntityCount
