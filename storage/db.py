"""
Database Models for Ayda Run

This module contains all SQLAlchemy models for the application.
Architecture supports:
- Unified Group model (standalone or within Club)
- Flexible visibility system
- Recurring activities
- Role-based permissions
- UUID-based primary keys for security
- Location-based filtering (country/city)
"""

from sqlalchemy import (
    create_engine, Column, Integer, BigInteger, String, DateTime,
    Boolean, Float, Enum as SQLEnum, ForeignKey, Text
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from datetime import datetime
from typing import Optional
from enum import Enum
import os
import uuid
from dotenv import load_dotenv

# Load .env file
load_dotenv()

from app_config.constants import DEFAULT_COUNTRY, DEFAULT_CITY

# Base class for models
Base = declarative_base()

# ============= ENUMS =============

class UserRole(str, Enum):
    """User roles in clubs/groups"""
    ADMIN = "admin"
    ORGANIZER = "organizer"
    TRAINER = "trainer"
    MEMBER = "member"

class SportType(str, Enum):
    """Types of sports activities"""
    RUNNING = "running"
    TRAIL = "trail"
    HIKING = "hiking"
    CYCLING = "cycling"
    YOGA = "yoga"
    WORKOUT = "workout"
    OTHER = "other"

class Difficulty(str, Enum):
    """Activity difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class ActivityVisibility(str, Enum):
    """Activity visibility types"""
    PRIVATE_GROUP = "private_group"     # Only group members
    PRIVATE_CLUB = "private_club"       # Only club members
    INVITE_ONLY = "invite_only"         # Only by link
    TELEGRAM_GROUP = "telegram_group"   # Telegram group members
    PUBLIC = "public"                   # Everyone

class ActivityStatus(str, Enum):
    """Activity status"""
    UPCOMING = "upcoming"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ParticipationStatus(str, Enum):
    """
    Participation status

    Flow:
    - REGISTERED: User signed up for activity (before start time)
    - CONFIRMED: Confirmed participation (legacy, same as registered)
    - AWAITING: Activity time passed, waiting for user confirmation
    - ATTENDED: User confirmed they participated
    - MISSED: User confirmed they missed the activity
    - COMPLETED: Legacy status
    - CANCELLED: User cancelled before activity
    """
    REGISTERED = "registered"
    CONFIRMED = "confirmed"
    AWAITING = "awaiting"      # Waiting for user to confirm attendance
    ATTENDED = "attended"      # User confirmed they attended
    MISSED = "missed"          # User confirmed they missed
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    PAID = "paid"
    NOT_REQUIRED = "not_required"

class ClubRequestStatus(str, Enum):
    """Club request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class JoinRequestStatus(str, Enum):
    """Join request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class MembershipStatus(str, Enum):
    """
    Membership status in club/group.

    Lifecycle:
    PENDING → ACTIVE → LEFT/KICKED/BANNED → (can return to ACTIVE)
                ↓
            ARCHIVED (soft-delete after 90 days inactive)

    See docs/next_steps/tggroup_sync_implementation_plan.md for details.
    """
    PENDING = "pending"      # Detected but not activated yet (e.g., from message parsing)
    ACTIVE = "active"        # Active member
    LEFT = "left"            # Left voluntarily
    KICKED = "kicked"        # Removed by admin
    BANNED = "banned"        # Banned from group
    ARCHIVED = "archived"    # Soft-deleted / inactive for too long


class MembershipSource(str, Enum):
    """How member was added to club/group"""
    ADMIN_IMPORT = "admin_import"           # Parsed from getChatAdministrators
    CHAT_MEMBER_EVENT = "chat_member_event" # chat_member webhook event
    MESSAGE_ACTIVITY = "message_activity"   # Passive tracking from messages
    MANUAL_REGISTRATION = "manual"          # User clicked "Join" button in app
    DEEP_LINK = "deep_link"                 # Joined via t.me/bot?start=join_xxx


# ============= MODELS =============

class User(Base):
    """User model - represents Telegram users"""
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)

    # Location
    country = Column(String(100), default=DEFAULT_COUNTRY, nullable=False)
    city = Column(String(100), default=DEFAULT_CITY, nullable=False, index=True)

    # Profile
    photo = Column(String(255), nullable=True)  # Telegram avatar file_id
    strava_link = Column(String(500), nullable=True)  # URL to Strava profile
    is_premium = Column(Boolean, default=False, nullable=False)
    show_photo = Column(Boolean, default=False, nullable=False)  # Show photo instead of initials

    # Onboarding
    has_completed_onboarding = Column(Boolean, default=False, nullable=False)
    preferred_sports = Column(Text, nullable=True)  # JSON array of sport IDs: ["running", "trail"]

    # Activity tracking
    first_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Demo data flag
    is_demo = Column(Boolean, default=False, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Strava integration (OAuth tokens encrypted at rest)
    strava_athlete_id = Column(BigInteger, unique=True, index=True, nullable=True)
    strava_access_token = Column(String(500), nullable=True)  # Encrypted
    strava_refresh_token = Column(String(500), nullable=True)  # Encrypted
    strava_token_expires_at = Column(DateTime, nullable=True)

    # Relationships
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    created_clubs = relationship("Club", back_populates="creator", foreign_keys="Club.creator_id")
    created_groups = relationship("Group", back_populates="creator", foreign_keys="Group.creator_id")
    created_activities = relationship("Activity", back_populates="creator", foreign_keys="Activity.creator_id")
    participations = relationship("Participation", back_populates="user", cascade="all, delete-orphan")

    @property
    def strava_connected(self):
        return self.strava_athlete_id is not None

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class Club(Base):
    """Club model - paid organizations with extended functionality"""
    __tablename__ = 'clubs'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    creator_id = Column(String(36), ForeignKey('users.id'), nullable=False)

    # Location
    country = Column(String(100), default=DEFAULT_COUNTRY, nullable=False)
    city = Column(String(100), nullable=False, index=True)

    # Telegram integration
    username = Column(String(255), nullable=True)  # @username
    telegram_chat_id = Column(BigInteger, nullable=True)
    invite_link = Column(String(500), nullable=True)  # t.me/... link
    photo = Column(String(255), nullable=True)  # Avatar file_id

    # Payment settings
    is_paid = Column(Boolean, default=False)
    price_per_activity = Column(Float, nullable=True)

    # Access control
    is_open = Column(Boolean, default=True, nullable=False)  # True = anyone can join

    # Telegram sync metadata
    bot_is_admin = Column(Boolean, default=False, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    telegram_member_count = Column(Integer, nullable=True)  # Total members in TG group
    sync_completed = Column(Boolean, default=False, nullable=False)  # All members collected?

    # Demo data flag
    is_demo = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="created_clubs", foreign_keys=[creator_id])
    groups = relationship("Group", back_populates="club", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="club")
    memberships = relationship("Membership", back_populates="club", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Club(name={self.name}, city={self.city})>"


class Group(Base):
    """
    Unified Group model - can be standalone or part of a club

    If club_id is NULL: standalone group (basic functionality)
    If club_id is set: group within club (extended functionality)
    """
    __tablename__ = 'groups'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Optional club relationship (NULL = standalone)
    club_id = Column(String(36), ForeignKey('clubs.id'), nullable=True, index=True)

    # Creator
    creator_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # Location
    country = Column(String(100), default=DEFAULT_COUNTRY, nullable=False)
    city = Column(String(100), nullable=False, index=True)

    # Telegram integration
    username = Column(String(255), nullable=True)  # @username
    telegram_chat_id = Column(BigInteger, nullable=True)
    invite_link = Column(String(500), nullable=True)  # t.me/... link
    photo = Column(String(255), nullable=True)  # Avatar file_id

    # Access control
    is_open = Column(Boolean, default=True)  # True = anyone can join

    # Demo data flag
    is_demo = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="created_groups", foreign_keys=[creator_id])
    club = relationship("Club", back_populates="groups")
    activities = relationship("Activity", back_populates="group")
    memberships = relationship("Membership", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Group(name={self.name}, city={self.city})>"


class Membership(Base):
    """
    Membership model - user's membership in club or group

    Either club_id or group_id must be set (not both)
    - club_id set: club-level membership
    - group_id set: group-level membership

    See MembershipStatus enum for lifecycle documentation.
    """
    __tablename__ = 'memberships'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # One of these must be set
    club_id = Column(String(36), ForeignKey('clubs.id'), nullable=True, index=True)
    group_id = Column(String(36), ForeignKey('groups.id'), nullable=True, index=True)

    # Role in the organization
    role = Column(SQLEnum(UserRole), default=UserRole.MEMBER, nullable=False)

    # Sync tracking fields
    status = Column(SQLEnum(MembershipStatus), default=MembershipStatus.ACTIVE, nullable=False, index=True)
    source = Column(SQLEnum(MembershipSource), default=MembershipSource.MANUAL_REGISTRATION, nullable=False)
    last_seen = Column(DateTime, nullable=True)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)  # When user left/was kicked

    # Relationships
    user = relationship("User", back_populates="memberships")
    club = relationship("Club", back_populates="memberships")
    group = relationship("Group", back_populates="memberships")

    def __repr__(self):
        return f"<Membership(user_id={self.user_id}, role={self.role}, status={self.status})>"


class RecurringTemplate(Base):
    """Template for recurring activities (e.g., every Monday, every weekend)"""
    __tablename__ = 'recurring_templates'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)

    # Schedule settings
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    time_of_day = Column(String(5), nullable=False)  # HH:MM format
    frequency = Column(Integer, default=4, nullable=False)  # 1-4 times per month (4=weekly, 2=bi-weekly, 1=monthly)
    total_occurrences = Column(Integer, nullable=False)  # Max 52 (1 year)
    generated_count = Column(Integer, default=0, nullable=False)  # How many activities created

    # Activity template fields
    description = Column(Text, nullable=True)
    location = Column(String(500), nullable=True)
    sport_type = Column(SQLEnum(SportType), nullable=False)
    difficulty = Column(SQLEnum(Difficulty), nullable=False)
    distance = Column(Float, nullable=True)  # in km
    duration = Column(Integer, nullable=True)  # in minutes
    max_participants = Column(Integer, nullable=True)

    # Organization (one of these must be set for recurring)
    club_id = Column(String(36), ForeignKey('clubs.id'), nullable=True, index=True)
    group_id = Column(String(36), ForeignKey('groups.id'), nullable=True, index=True)

    creator_id = Column(String(36), ForeignKey('users.id'), nullable=False)

    # Active status
    active = Column(Boolean, default=True)

    # Demo data flag
    is_demo = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    activities = relationship("Activity", back_populates="recurring_template")
    creator = relationship("User")
    club = relationship("Club")
    group = relationship("Group")

    def __repr__(self):
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        day_name = days[self.day_of_week] if self.day_of_week is not None else '?'
        return f"<RecurringTemplate(title={self.title}, day={day_name}, freq={self.frequency}x/month)>"


class Activity(Base):
    """Activity model - sports activities/events"""
    __tablename__ = 'activities'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False, index=True)
    location = Column(String(500), nullable=True)

    # Location
    country = Column(String(100), default=DEFAULT_COUNTRY, nullable=False)
    city = Column(String(100), nullable=False, index=True)

    # Relationships
    club_id = Column(String(36), ForeignKey('clubs.id'), nullable=True, index=True)
    group_id = Column(String(36), ForeignKey('groups.id'), nullable=True, index=True)
    creator_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    recurring_template_id = Column(String(36), ForeignKey('recurring_templates.id'), nullable=True)
    recurring_sequence = Column(Integer, nullable=True)  # Position in recurring series (1, 2, 3...)

    # Activity details
    sport_type = Column(SQLEnum(SportType), default=SportType.RUNNING, nullable=False, index=True)
    difficulty = Column(SQLEnum(Difficulty), default=Difficulty.MEDIUM, nullable=False)
    distance = Column(Float, nullable=True)  # in km
    duration = Column(Integer, nullable=True)  # in minutes
    max_participants = Column(Integer, nullable=True)

    # Visibility
    visibility = Column(SQLEnum(ActivityVisibility), default=ActivityVisibility.INVITE_ONLY, nullable=False, index=True)

    # Access control
    is_open = Column(Boolean, default=True, nullable=False)  # True = anyone can join

    # GPX file storage (in Telegram channel)
    gpx_file_id = Column(String(255), nullable=True)  # Telegram file_id for downloading
    gpx_filename = Column(String(255), nullable=True)  # Original filename
    gpx_file_message_id = Column(Integer, nullable=True)  # Message ID in GPX channel

    # Status
    status = Column(SQLEnum(ActivityStatus), default=ActivityStatus.UPCOMING, nullable=False, index=True)

    # Demo data flag
    is_demo = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    club = relationship("Club", back_populates="activities")
    group = relationship("Group", back_populates="activities")
    creator = relationship("User", back_populates="created_activities", foreign_keys=[creator_id])
    recurring_template = relationship("RecurringTemplate", back_populates="activities")
    participations = relationship("Participation", back_populates="activity", cascade="all, delete-orphan")
    join_requests = relationship("JoinRequest", back_populates="activity", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Activity(title={self.title}, city={self.city}, date={self.date})>"


class Participation(Base):
    """Participation model - user's participation in an activity"""
    __tablename__ = 'participations'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    activity_id = Column(String(36), ForeignKey('activities.id'), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # Participation status
    status = Column(SQLEnum(ParticipationStatus), default=ParticipationStatus.REGISTERED, nullable=False)

    # Did they actually show up? None = not marked, True = attended, False = missed
    attended = Column(Boolean, default=None, nullable=True)

    # Payment tracking (for paid clubs)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.NOT_REQUIRED, nullable=False)

    registered_at = Column(DateTime, default=datetime.utcnow)

    # Training link tracking (post-training flow)
    training_link = Column(String(500), nullable=True)  # URL to Strava/Garmin/etc
    training_link_source = Column(String(20), nullable=True)  # "manual" | "strava_auto"
    strava_activity_id = Column(BigInteger, nullable=True)  # Strava activity ID
    strava_activity_data = Column(Text, nullable=True)  # JSON with distance, time, etc.

    # Relationships
    activity = relationship("Activity", back_populates="participations")
    user = relationship("User", back_populates="participations")

    def __repr__(self):
        return f"<Participation(activity_id={self.activity_id}, user_id={self.user_id}, status={self.status})>"


class PostTrainingNotificationStatus(str, Enum):
    """Status of post-training notification"""
    SENT = "sent"                    # Initial notification sent
    LINK_SUBMITTED = "link_submitted"  # User submitted training link
    NOT_ATTENDED = "not_attended"    # User confirmed they didn't attend
    REMINDER_SENT = "reminder_sent"  # Reminder was sent


class PostTrainingNotification(Base):
    """
    Post-Training Notification model - tracks notification status for each participant.

    Created when activity ends and notification is sent to participant.
    Tracks whether user submitted link, confirmed non-attendance, or needs reminder.
    """
    __tablename__ = 'post_training_notifications'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    activity_id = Column(String(36), ForeignKey('activities.id'), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # Notification status
    status = Column(SQLEnum(PostTrainingNotificationStatus), default=PostTrainingNotificationStatus.SENT, nullable=False)

    # Timestamps
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    # Reminder tracking
    reminder_count = Column(Integer, default=0, nullable=False)

    # Relationships
    activity = relationship("Activity")
    user = relationship("User")

    def __repr__(self):
        return f"<PostTrainingNotification(activity_id={self.activity_id}, user_id={self.user_id}, status={self.status})>"


class ClubRequest(Base):
    """
    Club Request model - requests from organizers to create clubs

    Used for manual moderation of club creation during beta phase.
    """
    __tablename__ = 'club_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # Club data
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sports = Column(Text, nullable=True)  # JSON array of sport IDs
    members_count = Column(Integer, nullable=True)
    groups_count = Column(Integer, nullable=True)
    telegram_group_link = Column(String(500), nullable=True)
    contact = Column(String(255), nullable=True)

    # Access control
    is_open = Column(Boolean, default=True, nullable=False)  # True = anyone can join

    # Request status
    status = Column(SQLEnum(ClubRequestStatus), default=ClubRequestStatus.PENDING, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<ClubRequest(name={self.name}, status={self.status})>"


class AnalyticsEvent(Base):
    """
    Analytics Event model - tracks user actions for internal analytics.

    Events:
    - screen_view: User opened a screen
    - activity_create: User created an activity
    - activity_join: User registered for activity
    - activity_cancel: User cancelled registration
    - activity_attend: User confirmed attendance
    - club_join / group_join: User joined club/group
    - onboarding_step: User completed onboarding step
    - onboarding_complete: User finished onboarding
    - gpx_download: User downloaded GPX file
    """
    __tablename__ = 'analytics_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True, index=True)

    # Event data
    event_name = Column(String(100), nullable=False, index=True)
    event_params = Column(Text, nullable=True)  # JSON string: {"screen_name": "home"}

    # Session tracking
    session_id = Column(String(36), nullable=True, index=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<AnalyticsEvent(event={self.event_name}, user_id={self.user_id})>"


class JoinRequest(Base):
    """
    Join Request model - user's request to join a closed club/group/activity

    Used when a club/group/activity is marked as is_open=False.
    Organizer can approve or reject the request.
    """
    __tablename__ = 'join_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    # One of these must be set (entity being requested)
    club_id = Column(String(36), ForeignKey('clubs.id'), nullable=True, index=True)
    group_id = Column(String(36), ForeignKey('groups.id'), nullable=True, index=True)
    activity_id = Column(String(36), ForeignKey('activities.id'), nullable=True, index=True)

    # Request status
    status = Column(SQLEnum(JoinRequestStatus), default=JoinRequestStatus.PENDING, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # Auto-reject after this time

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    club = relationship("Club", foreign_keys=[club_id])
    group = relationship("Group", foreign_keys=[group_id])
    activity = relationship("Activity", back_populates="join_requests", foreign_keys=[activity_id])

    def __repr__(self):
        entity = "club" if self.club_id else "group" if self.group_id else "activity"
        return f"<JoinRequest(user_id={self.user_id}, {entity}, status={self.status})>"


class Feedback(Base):
    """
    User Feedback model - stores feedback messages from users.

    Users can send text messages to the bot in private chat,
    and they will be saved here and forwarded to the feedback group.
    """
    __tablename__ = 'feedback'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=True, index=True)
    telegram_id = Column(BigInteger, nullable=False, index=True)

    # Message content
    message = Column(Text, nullable=False)
    message_id = Column(Integer, nullable=True)  # Telegram message ID

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        preview = self.message[:50] + "..." if len(self.message) > 50 else self.message
        return f"<Feedback(telegram_id={self.telegram_id}, message='{preview}')>"


class StravaWebhookEvent(Base):
    """Log of processed Strava webhook events for idempotency."""
    __tablename__ = 'strava_webhook_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
    strava_activity_id = Column(BigInteger, unique=True, nullable=False, index=True)
    strava_athlete_id = Column(BigInteger, nullable=False, index=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    result = Column(String(50))  # "matched", "no_match", "already_linked", "error", "pending_retry"
    retry_count = Column(Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<StravaWebhookEvent(strava_activity_id={self.strava_activity_id}, result={self.result})>"


class PendingStravaMatch(Base):
    """Temporary storage for pending Strava match confirmations."""
    __tablename__ = 'pending_strava_matches'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    activity_id = Column(String(36), ForeignKey('activities.id'), nullable=False)
    strava_activity_id = Column(BigInteger, nullable=False)
    strava_activity_data = Column(Text, nullable=True)  # JSON cache of Strava activity
    confidence = Column(String(20), nullable=False)  # "high" | "medium"
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Auto-cleanup after 24h

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    activity = relationship("Activity", foreign_keys=[activity_id])

    def __repr__(self):
        return f"<PendingStravaMatch(user_id={self.user_id}, activity_id={self.activity_id}, confidence={self.confidence})>"


# ============= DATABASE SETUP =============

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/ayda")

# Fix for Render/Railway's postgres:// URL (SQLAlchemy requires postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

def get_db():
    """Get database session (for FastAPI dependency injection)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============= HELPER FUNCTIONS =============

def get_or_create_user(db: Session, telegram_id: int, username: str = None, first_name: str = None) -> User:
    """
    Get existing user or create new one using provided session
    """
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update user info if changed
        # Note: In a real app we might want to be careful about auto-updating
        if username and user.username != username:
            user.username = username
        if first_name and user.first_name != first_name:
            user.first_name = first_name
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
    return user

def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """Get user by Telegram ID"""
    session = SessionLocal()
    try:
        return session.query(User).filter(User.telegram_id == telegram_id).first()
    finally:
        session.close()
