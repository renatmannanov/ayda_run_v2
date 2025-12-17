from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from .common import BaseResponse

class ClubCreate(BaseModel):
    """Schema for creating club"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_paid: bool = Field(default=False)
    price_per_activity: Optional[float] = Field(None, ge=0, le=10000)
    telegram_chat_id: Optional[str] = None

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

class ClubResponse(BaseResponse):
    """Schema for club response"""
    name: str
    description: Optional[str]
    is_paid: bool
    price_per_activity: Optional[float]
    telegram_chat_id: Optional[str]
    creator_id: int

    # Computed
    members_count: int = 0
    groups_count: int = 0
    is_member: bool = False
    user_role: Optional[str] = None
