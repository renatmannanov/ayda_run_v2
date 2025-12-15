from pydantic import BaseModel, Field
from typing import Optional
from .common import BaseResponse, UserRole

class GroupCreate(BaseModel):
    """Schema for creating group"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    club_id: Optional[int] = None
    telegram_chat_id: Optional[str] = None

class GroupUpdate(BaseModel):
    """Schema for updating group"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)

class GroupResponse(BaseResponse):
    """Schema for group response"""
    name: str
    description: Optional[str]
    club_id: Optional[int]
    telegram_chat_id: Optional[str]
    telegram_chat_id: Optional[str]
    
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
    user_id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    name: str
    role: UserRole
    joined_at: Optional[str] = None  # datetime to str if needed
