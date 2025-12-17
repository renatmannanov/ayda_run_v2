"""
Common Pydantic schemas and validators
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum

class SportType(str, Enum):
    RUNNING = "running"
    TRAIL = "trail"
    HIKING = "hiking"
    CYCLING = "cycling"
    OTHER = "other"

class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class ActivityVisibility(str, Enum):
    PRIVATE_GROUP = "private_group"     # Only group members
    PRIVATE_CLUB = "private_club"       # Only club members
    INVITE_ONLY = "invite_only"         # Only by link
    TELEGRAM_GROUP = "telegram_group"   # Telegram group members
    PUBLIC = "public"                   # Everyone

class ActivityStatus(str, Enum):
    UPCOMING = "upcoming"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class UserRole(str, Enum):
    MEMBER = "member"
    TRAINER = "trainer"
    ORGANIZER = "organizer"
    ADMIN = "admin"

class ParticipationStatus(str, Enum):
    REGISTERED = "registered"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    WAITLIST = "waitlist"

class PaymentStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"

# Base response model
class BaseResponse(BaseModel):
    """Base response with common fields"""
    id: str  # UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
