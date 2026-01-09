"""
Analytics Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AnalyticsEventCreate(BaseModel):
    """Schema for creating analytics event"""
    event_name: str = Field(..., min_length=1, max_length=100)
    event_params: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = Field(None, max_length=36)


class AnalyticsEventResponse(BaseModel):
    """Schema for analytics event response"""
    id: int
    user_id: Optional[str]
    event_name: str
    event_params: Optional[Dict[str, Any]]
    session_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsEventBatch(BaseModel):
    """Schema for batch analytics events (for offline sync)"""
    events: list[AnalyticsEventCreate] = Field(..., max_length=100)
