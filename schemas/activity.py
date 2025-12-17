from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo
from datetime import datetime
from typing import Optional
from .common import SportType, Difficulty, BaseResponse, ActivityVisibility, ActivityStatus

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
    club_id: Optional[str] = None  # UUID
    group_id: Optional[str] = None  # UUID

    @field_validator('date')
    @classmethod
    def date_must_be_future(cls, v: datetime) -> datetime:
        """Activity date must be in the future"""
        if v < datetime.now():
            raise ValueError('Activity date must be in the future')
        return v

    @field_validator('group_id')
    @classmethod
    def cannot_have_both_club_and_group(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        """Activity cannot belong to both club and group"""
        if v and info.data.get('club_id'):
            raise ValueError('Activity cannot belong to both club and group')
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
    """Schema for updating activity"""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    date: Optional[datetime] = None
    location: Optional[str] = Field(None, min_length=2, max_length=200)
    sport_type: Optional[SportType] = None
    difficulty: Optional[Difficulty] = None
    distance: Optional[float] = Field(None, ge=0, le=500)
    duration: Optional[int] = Field(None, ge=1, le=1440)
    max_participants: Optional[int] = Field(None, ge=1, le=1000)
    visibility: Optional[ActivityVisibility] = None
    status: Optional[ActivityStatus] = None

    @field_validator('date')
    @classmethod
    def date_must_be_future(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v < datetime.now():
            raise ValueError('Activity date must be in the future')
        return v

class ActivityResponse(BaseResponse):
    """Schema for activity response"""
    title: str
    description: Optional[str]
    date: datetime
    location: Optional[str]

    # Location
    country: str
    city: str

    sport_type: SportType
    difficulty: Difficulty
    distance: Optional[float]
    duration: Optional[int]
    max_participants: Optional[int]
    visibility: ActivityVisibility
    status: ActivityStatus
    club_id: Optional[str]  # UUID
    group_id: Optional[str]  # UUID
    creator_id: str  # UUID

    # Computed fields
    participants_count: int = 0
    is_joined: bool = False
    club_name: Optional[str] = None
    group_name: Optional[str] = None
