from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .common import ParticipationStatus

class UserResponse(BaseModel):
    """Response model for user"""
    model_config = {"from_attributes": True}

    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    has_completed_onboarding: bool
    preferred_sports: Optional[str]  # JSON string
    created_at: datetime

class ParticipantResponse(BaseModel):
    """Response model for participant"""
    model_config = {"from_attributes": True}

    user_id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    name: str  # Display name for frontend
    status: ParticipationStatus
    attended: bool
    registered_at: datetime
