"""
Join Request Schemas

Schemas for join request operations - when users request to join closed clubs/groups/activities
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .common import BaseResponse


class JoinRequestCreate(BaseModel):
    """
    Schema for creating join request

    Note: entity_id (club_id, group_id, or activity_id) is passed through URL
    """
    pass


class JoinRequestResponse(BaseResponse):
    """Schema for join request response"""
    user_id: str  # UUID
    club_id: Optional[str] = None  # UUID
    group_id: Optional[str] = None  # UUID
    activity_id: Optional[str] = None  # UUID
    status: str  # pending, approved, rejected, expired
    expires_at: Optional[datetime] = None

    # User info (for organizer to see)
    user_name: Optional[str] = None
    username: Optional[str] = None
    user_first_name: Optional[str] = None
    user_sports: Optional[str] = None  # JSON string
    user_strava_link: Optional[str] = None

    # Entity info
    entity_name: Optional[str] = None  # Club/Group/Activity name
    entity_type: Optional[str] = None  # "club", "group", "activity"


class JoinRequestAction(BaseModel):
    """
    Schema for approving/rejecting join request

    Note: action (approve/reject) is determined by the endpoint URL
    """
    pass
