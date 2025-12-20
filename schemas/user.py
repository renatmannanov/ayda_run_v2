from pydantic import BaseModel, field_serializer, ConfigDict
from typing import Optional
from datetime import datetime
from .common import ParticipationStatus

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
    photo: Optional[str]  # Telegram avatar file_id
    strava_link: Optional[str]  # URL to Strava profile
    is_premium: bool

    # Onboarding
    has_completed_onboarding: bool
    preferred_sports: Optional[str]  # JSON string

    # Activity tracking
    first_seen_at: datetime
    last_seen_at: datetime

    # Timestamps
    created_at: datetime

class UserProfileUpdate(BaseModel):
    """Request model for updating user profile"""
    photo: Optional[str] = None  # Telegram file_id or URL
    strava_link: Optional[str] = None  # URL to Strava profile

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
    attended: bool
    registered_at: datetime
    preferred_sports: Optional[str] = None  # JSON string of sport preferences

    @field_serializer('telegram_id', when_used='always')
    def serialize_telegram_id(self, telegram_id: int | str) -> str:
        """Convert telegram_id to string for JSON safety"""
        return str(telegram_id)
