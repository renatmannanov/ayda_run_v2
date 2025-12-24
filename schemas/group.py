from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from .common import BaseResponse, UserRole

class GroupCreate(BaseModel):
    """Schema for creating group"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    club_id: Optional[str] = None  # UUID

    # Location (both optional - will use user's location if not provided)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    country: Optional[str] = Field(None, max_length=100)

    # Telegram
    username: Optional[str] = Field(None, max_length=255)
    telegram_chat_id: Optional[str] = None
    invite_link: Optional[str] = Field(None, max_length=500)
    photo: Optional[str] = Field(None, max_length=255)

class GroupUpdate(BaseModel):
    """Schema for updating group.

    Note: telegram_chat_id and club_id are immutable after creation.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    # telegram_chat_id is immutable - cannot be changed after linking
    # club_id is immutable - cannot change group's club affiliation
    is_open: Optional[bool] = None

class GroupResponse(BaseResponse):
    """Schema for group response"""
    name: str
    description: Optional[str]
    club_id: Optional[str]  # UUID

    # Location
    country: str
    city: str

    # Telegram
    username: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    invite_link: Optional[str] = None
    photo: Optional[str] = None

    # Access control
    is_open: bool

    # Computed
    members_count: int = 0
    is_member: bool = False
    club_name: Optional[str] = None
    user_role: Optional[str] = None

class MembershipUpdate(BaseModel):
    """Schema for updating member role"""
    role: UserRole

class MemberResponse(BaseModel):
    """Schema for list of members"""
    user_id: str  # UUID
    telegram_id: int | str  # Accept int from DB, serialize to string for JSON
    username: Optional[str]
    first_name: Optional[str]
    name: str
    photo: Optional[str] = None  # Telegram file_id or URL
    show_photo: bool = False  # Show photo instead of initials
    role: UserRole
    joined_at: Optional[str] = None  # datetime to str if needed
    preferred_sports: Optional[str] = None  # JSON string of sport preferences

    @field_serializer('telegram_id', when_used='always')
    def serialize_telegram_id(self, telegram_id: int | str) -> str:
        """Convert telegram_id to string for JSON safety"""
        return str(telegram_id)
