from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from .common import BaseResponse

class ClubCreate(BaseModel):
    """Schema for creating club"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

    # Location (both optional - will use user's location if not provided)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    country: Optional[str] = Field(None, max_length=100)

    # Telegram
    username: Optional[str] = Field(None, max_length=255)
    telegram_chat_id: Optional[int] = None
    invite_link: Optional[str] = Field(None, max_length=500)
    photo: Optional[str] = Field(None, max_length=255)

    # Payment
    is_paid: bool = Field(default=False)
    price_per_activity: Optional[float] = Field(None, ge=0, le=10000)

    # Access control
    is_open: bool = Field(default=True, description="True = anyone can join, False = join by request")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Беговой клуб Алматы",
                "description": "Дружеский беговой клуб для всех уровней",
                "is_paid": False
            }
        }
    )

class ClubUpdate(BaseModel):
    """Schema for updating club"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_paid: Optional[bool] = None
    price_per_activity: Optional[float] = Field(None, ge=0, le=10000)
    is_open: Optional[bool] = None

class ClubResponse(BaseResponse):
    """Schema for club response"""
    name: str
    description: Optional[str]

    # Location
    country: str
    city: str

    # Telegram
    username: Optional[str]
    telegram_chat_id: Optional[int]
    invite_link: Optional[str]
    photo: Optional[str]

    # Payment
    is_paid: bool
    price_per_activity: Optional[float]

    # Access control
    is_open: bool

    creator_id: str  # UUID

    # Computed
    members_count: int = 0
    groups_count: int = 0
    is_member: bool = False
    user_role: Optional[str] = None
