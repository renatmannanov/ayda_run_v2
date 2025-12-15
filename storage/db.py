"""
Database Models for Ayda Run

This module contains all SQLAlchemy models for the application.
Architecture supports:
- Unified Group model (standalone or within Club)
- Flexible visibility system
- Recurring activities
- Role-based permissions
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime,
    Boolean, Float, Enum as SQLEnum, ForeignKey, Text
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
from typing import Optional
from enum import Enum
import os

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
    """Participation status"""
    REGISTERED = "registered"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    """Payment status"""
    PENDING = "pending"
    PAID = "paid"
    NOT_REQUIRED = "not_required"

# ============= MODELS =============

class User(Base):
    """User model - represents Telegram users"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    has_completed_onboarding = Column(Boolean, default=False, nullable=False)
    preferred_sports = Column(Text, nullable=True)  # JSON array of sport IDs: ["running", "trail"]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    created_clubs = relationship("Club", back_populates="creator", foreign_keys="Club.creator_id")
    created_activities = relationship("Activity", back_populates="creator", foreign_keys="Activity.creator_id")
    participations = relationship("Participation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class Club(Base):
    """Club model - paid organizations with extended functionality"""
    __tablename__ = 'clubs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Payment settings
    is_paid = Column(Boolean, default=False)
    price_per_activity = Column(Float, nullable=True)
    
    # Telegram integration
    telegram_chat_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="created_clubs", foreign_keys=[creator_id])
    groups = relationship("Group", back_populates="club", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="club")
    memberships = relationship("Membership", back_populates="club", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Club(name={self.name}, is_paid={self.is_paid})>"


class Group(Base):
    """
    Unified Group model - can be standalone or part of a club
    
    If club_id is NULL: standalone group (basic functionality)
    If club_id is set: group within club (extended functionality)
    """
    __tablename__ = 'groups'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Optional club relationship (NULL = standalone)
    club_id = Column(Integer, ForeignKey('clubs.id'), nullable=True, index=True)
    
    # Telegram integration
    telegram_chat_id = Column(Integer, nullable=True)
    
    # Access control
    is_open = Column(Boolean, default=True)  # True = anyone can join
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    club = relationship("Club", back_populates="groups")
    activities = relationship("Activity", back_populates="group")
    memberships = relationship("Membership", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Group(name={self.name}, club_id={self.club_id})>"


class Membership(Base):
    """
    Membership model - user's membership in club or group
    
    Either club_id or group_id must be set (not both)
    - club_id set: club-level membership
    - group_id set: group-level membership
    """
    __tablename__ = 'memberships'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # One of these must be set
    club_id = Column(Integer, ForeignKey('clubs.id'), nullable=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True, index=True)
    
    # Role in the organization
    role = Column(SQLEnum(UserRole), default=UserRole.MEMBER, nullable=False)
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="memberships")
    club = relationship("Club", back_populates="memberships")
    group = relationship("Group", back_populates="memberships")
    
    def __repr__(self):
        return f"<Membership(user_id={self.user_id}, role={self.role})>"


class RecurringTemplate(Base):
    """Template for recurring activities (e.g., every Monday, every weekend)"""
    __tablename__ = 'recurring_templates'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    
    # Recurrence rule (e.g., "WEEKLY:MON,THU,SAT")
    recurrence_rule = Column(String(255), nullable=False)
    
    # Organization (one of these can be set)
    club_id = Column(Integer, ForeignKey('clubs.id'), nullable=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True, index=True)
    
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Active status
    active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    activities = relationship("Activity", back_populates="recurring_template")
    
    def __repr__(self):
        return f"<RecurringTemplate(title={self.title}, rule={self.recurrence_rule})>"


class Activity(Base):
    """Activity model - sports activities/events"""
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False, index=True)
    location = Column(String(500), nullable=True)
    
    # Relationships
    club_id = Column(Integer, ForeignKey('clubs.id'), nullable=True, index=True)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=True, index=True)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    recurring_template_id = Column(Integer, ForeignKey('recurring_templates.id'), nullable=True)
    
    # Activity details
    sport_type = Column(SQLEnum(SportType), default=SportType.RUNNING, nullable=False)
    difficulty = Column(SQLEnum(Difficulty), default=Difficulty.MEDIUM, nullable=False)
    distance = Column(Float, nullable=True)  # in km
    duration = Column(Integer, nullable=True)  # in minutes
    max_participants = Column(Integer, nullable=True)
    
    # Visibility
    visibility = Column(SQLEnum(ActivityVisibility), default=ActivityVisibility.INVITE_ONLY, nullable=False, index=True)
    
    # GPX file storage (in Telegram channel)
    gpx_file_channel_id = Column(Integer, nullable=True)
    gpx_file_message_id = Column(Integer, nullable=True)
    
    # Status
    status = Column(SQLEnum(ActivityStatus), default=ActivityStatus.UPCOMING, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    club = relationship("Club", back_populates="activities")
    group = relationship("Group", back_populates="activities")
    creator = relationship("User", back_populates="created_activities", foreign_keys=[creator_id])
    recurring_template = relationship("RecurringTemplate", back_populates="activities")
    participations = relationship("Participation", back_populates="activity", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Activity(title={self.title}, date={self.date}, status={self.status})>"


class Participation(Base):
    """Participation model - user's participation in an activity"""
    __tablename__ = 'participations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    activity_id = Column(Integer, ForeignKey('activities.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    
    # Participation status
    status = Column(SQLEnum(ParticipationStatus), default=ParticipationStatus.REGISTERED, nullable=False)
    
    # Did they actually show up?
    attended = Column(Boolean, default=False)
    
    # Payment tracking (for paid clubs)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.NOT_REQUIRED, nullable=False)
    
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    activity = relationship("Activity", back_populates="participations")
    user = relationship("User", back_populates="participations")
    
    def __repr__(self):
        return f"<Participation(activity_id={self.activity_id}, user_id={self.user_id}, status={self.status})>"


# ============= DATABASE SETUP =============

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

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
