from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .common import ParticipationStatus

class UserResponse(BaseModel):
    """Response model for user"""
    model_config = {"from_attributes": True}

    id: str  # UUID
    telegram_id: str  # String for JSON/JS safety (64-bit int)
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]

    # Location
    country: str
    city: str

    # Profile
    photo: Optional[str]  # Telegram avatar file_id
    is_premium: bool

    # Onboarding
    has_completed_onboarding: bool
    preferred_sports: Optional[str]  # JSON string

    # Activity tracking
    first_seen_at: datetime
    last_seen_at: datetime

    # Timestamps
    created_at: datetime

class ParticipantResponse(BaseModel):
    """Response model for participant"""
    model_config = {"from_attributes": True}

    user_id: str  # UUID
    telegram_id: str  # String for JSON/JS safety
    username: Optional[str]
    first_name: Optional[str]
    name: str  # Display name for frontend
    status: ParticipationStatus
    attended: bool
    registered_at: datetime
