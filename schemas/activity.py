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
        """Activity date must be in the future"""
        if v < datetime.now():
            raise ValueError('Activity date must be in the future')
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
    is_open: Optional[bool] = None
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
    is_open: bool
    status: ActivityStatus
    club_id: Optional[str]  # UUID
    group_id: Optional[str]  # UUID
    creator_id: str  # UUID

    # Computed fields
    participants_count: int = 0
    is_joined: bool = False
    can_view_participants: bool = True  # False if closed and not member
    can_download_gpx: bool = True  # False if closed and not member
    club_name: Optional[str] = None
    group_name: Optional[str] = None
