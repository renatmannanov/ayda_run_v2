"""
API Server - FastAPI Backend for Ayda Run

Provides REST API for:
- Activities (CRUD)
- Participation (join/leave)
- Static file serving for webapp
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime

from storage.db import (
    init_db, get_db, Activity, Participation, User,
    SportType, Difficulty, ActivityVisibility, ActivityStatus,
    ParticipationStatus, PaymentStatus
)
from auth import get_current_user, get_current_user_optional
from permissions import can_create_activity_in_club, can_create_activity_in_group, require_activity_owner

app = FastAPI(title="Ayda Run API", version="1.0.0")

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.rate_limit_global]
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom rate limit error response"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "Вы превысили лимит запросов. Пожалуйста, попробуйте позже.",
            "retry_after": str(exc.limit) 
        }, # exc.detail sometimes is not what we expect in some versions, using exc.limit or generic message is safer, but plan suggests exc.detail check if it works.
        headers={
            "Retry-After": "60" # Default fallback
        }
    )


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables"""
    init_db()
    print("[SUCCESS] Database initialized")

# ============================================================================
# Pydantic Models (Request/Response)
# ============================================================================

class ActivityCreate(BaseModel):
    """Request model for creating activity"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    date: datetime
    location: Optional[str] = Field(None, max_length=500)
    club_id: Optional[int] = None
    group_id: Optional[int] = None
    sport_type: SportType = SportType.RUNNING
    difficulty: Difficulty = Difficulty.MEDIUM
    distance: Optional[float] = Field(None, gt=0)
    duration: Optional[int] = Field(None, gt=0)
    max_participants: Optional[int] = Field(None, gt=0)
    visibility: ActivityVisibility = ActivityVisibility.INVITE_ONLY


class ActivityUpdate(BaseModel):
    """Request model for updating activity"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    date: Optional[datetime] = None
    location: Optional[str] = Field(None, max_length=500)
    sport_type: Optional[SportType] = None
    difficulty: Optional[Difficulty] = None
    distance: Optional[float] = Field(None, gt=0)
    duration: Optional[int] = Field(None, gt=0)
    max_participants: Optional[int] = Field(None, gt=0)
    visibility: Optional[ActivityVisibility] = None
    status: Optional[ActivityStatus] = None


class ActivityResponse(BaseModel):
    """Response model for activity"""
    model_config = {"from_attributes": True}
    
    id: int
    title: str
    description: Optional[str]
    date: datetime
    location: Optional[str]
    club_id: Optional[int]
    group_id: Optional[int]
    creator_id: int
    sport_type: SportType
    difficulty: Difficulty
    distance: Optional[float]
    duration: Optional[int]
    max_participants: Optional[int]
    visibility: ActivityVisibility
    status: ActivityStatus
    created_at: datetime
    participants_count: int = 0
    is_joined: bool = False
    club_name: Optional[str] = None
    group_name: Optional[str] = None


class ParticipantResponse(BaseModel):
    """Response model for participant"""
    model_config = {"from_attributes": True}

    user_id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    name: str  # Display name for frontend
    status: ParticipationStatus
    attended: bool
    registered_at: datetime


# ============================================================================
# Static File Serving
# ============================================================================

@app.get("/")
async def root():
    """Serve the main webapp page"""
    return FileResponse("webapp/dist/index.html")

# Serve all static files from dist folder
from fastapi.staticfiles import StaticFiles
import os

# Mount static files directory
if os.path.exists("webapp/dist"):
    app.mount("/assets", StaticFiles(directory="webapp/dist/assets"), name="assets")

# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Ayda Run API"}

# ============================================================================
# Users API
# ============================================================================

class UserResponse(BaseModel):
    """Response model for user"""
    model_config = {"from_attributes": True}

    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    has_completed_onboarding: bool
    preferred_sports: Optional[str]  # JSON string: '["running", "trail"]'
    created_at: datetime

@app.get("/api/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


class OnboardingData(BaseModel):
    """Request model for completing onboarding"""
    preferred_sports: Optional[list[str]] = None  # e.g., ["running", "trail"]


@app.patch("/api/users/me/onboarding", response_model=UserResponse)
async def complete_onboarding(
    onboarding_data: OnboardingData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete user onboarding and save preferences"""
    import json

    # Update onboarding status
    current_user.has_completed_onboarding = True

    # Save preferred sports as JSON string
    if onboarding_data.preferred_sports:
        current_user.preferred_sports = json.dumps(onboarding_data.preferred_sports)

    db.commit()
    db.refresh(current_user)

    return current_user

# ============================================================================
# Activities API
# ============================================================================

@app.post("/api/activities", response_model=ActivityResponse, status_code=201)
@limiter.limit(settings.rate_limit_create)
async def create_activity(
    request: Request,
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new activity
    
    - Standalone activity: anyone can create
    - Club activity: requires organizer role
    - Group activity: requires appropriate permissions
    """
    # Check permissions for club/group activities
    if activity_data.club_id:
        if not can_create_activity_in_club(db, current_user, activity_data.club_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to create activity in this club"
            )
    
    if activity_data.group_id:
        if not can_create_activity_in_group(db, current_user, activity_data.group_id):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to create activity in this group"
            )
    
    # Create activity
    activity = Activity(
        **activity_data.model_dump(),
        creator_id=current_user.id,
        status=ActivityStatus.UPCOMING
    )
    
    db.add(activity)
    db.commit()
    db.refresh(activity)
    
    # Convert to response
    response = ActivityResponse.model_validate(activity)
    response.participants_count = 0
    response.is_joined = False
    
    return response


@app.get("/api/activities", response_model=List[ActivityResponse])
@limiter.limit(settings.rate_limit_read)
async def list_activities(
    request: Request,
    club_id: Optional[int] = Query(None),
    group_id: Optional[int] = Query(None),
    sport_type: Optional[SportType] = Query(None),
    difficulty: Optional[Difficulty] = Query(None),
    visibility: Optional[ActivityVisibility] = Query(None),
    status: ActivityStatus = Query(ActivityStatus.UPCOMING),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    List activities with filters
    
    - Public activities visible to all
    - Private activities only to members
    - Invite-only via direct link
    """
    query = db.query(Activity)
    
    # Apply filters
    if club_id:
        query = query.filter(Activity.club_id == club_id)
    if group_id:
        query = query.filter(Activity.group_id == group_id)
    if sport_type:
        query = query.filter(Activity.sport_type == sport_type)
    if difficulty:
        query = query.filter(Activity.difficulty == difficulty)
    if visibility:
        query = query.filter(Activity.visibility == visibility)
    if status:
        query = query.filter(Activity.status == status)
    
    # Visibility filtering (simplified for MVP - only PUBLIC and INVITE_ONLY)
    if not current_user:
        # Non-authenticated users only see public activities
        query = query.filter(Activity.visibility == ActivityVisibility.PUBLIC)
    
    # Order by date
    query = query.order_by(Activity.date.asc())
    
    # Eager load relationships
    query = query.options(joinedload(Activity.club), joinedload(Activity.group))

    # Pagination
    activities = query.offset(offset).limit(limit).all()
    
    # Convert to response with participant counts
    result = []
    print(f"[DEBUG] Processing {len(activities)} activities") 
    for activity in activities:
        response = ActivityResponse.model_validate(activity)
        # ... (rest of loop)
        response.participants_count = db.query(Participation).filter(
            Participation.activity_id == activity.id,
            Participation.status.in_([ParticipationStatus.REGISTERED, ParticipationStatus.CONFIRMED])
        ).count()
        
        if current_user:
            participation = db.query(Participation).filter(
                Participation.activity_id == activity.id,
                Participation.user_id == current_user.id
            ).first()
            response.is_joined = participation is not None
        
        # Populate names (eager loaded now)
        if activity.club:
            response.club_name = activity.club.name
            print(f"[DEBUG] Activity {activity.id}: Set club_name='{activity.club.name}'")
        if activity.group:
            response.group_name = activity.group.name
            print(f"[DEBUG] Activity {activity.id}: Set group_name='{activity.group.name}'")

        result.append(response)
    
    return result


@app.get("/api/activities/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get activity details by ID"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Convert to response
    response = ActivityResponse.model_validate(activity)
    response.participants_count = db.query(Participation).filter(
        Participation.activity_id == activity.id,
        Participation.status.in_([ParticipationStatus.REGISTERED, ParticipationStatus.CONFIRMED])
    ).count()
    
    if current_user:
        participation = db.query(Participation).filter(
            Participation.activity_id == activity.id,
            Participation.user_id == current_user.id
        ).first()
        response.is_joined = participation is not None
    
    # Populate names
    if activity.club:
        response.club_name = activity.club.name
    if activity.group:
        response.group_name = activity.group.name
    
    return response


@app.patch("/api/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: int,
    activity_data: ActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update activity (only creator can update)"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check permissions
    require_activity_owner(current_user, activity)
    
    # Update fields
    update_data = activity_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(activity, field, value)
    
    db.commit()
    db.refresh(activity)
    
    # Convert to response
    response = ActivityResponse.model_validate(activity)
    response.participants_count = db.query(Participation).filter(
        Participation.activity_id == activity.id,
        Participation.status.in_([ParticipationStatus.REGISTERED, ParticipationStatus.CONFIRMED])
    ).count()
    
    participation = db.query(Participation).filter(
        Participation.activity_id == activity.id,
        Participation.user_id == current_user.id
    ).first()
    response.is_joined = participation is not None
    
    return response


@app.delete("/api/activities/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete activity (only creator can delete)"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check permissions
    require_activity_owner(current_user, activity)
    
    db.delete(activity)
    db.commit()
    
    return None

# ============================================================================
# Participation API
# ============================================================================

@app.post("/api/activities/{activity_id}/join", status_code=201)
async def join_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join an activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check if already joined
    existing = db.query(Participation).filter(
        Participation.activity_id == activity_id,
        Participation.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already joined this activity")
    
    # Check max participants
    if activity.max_participants:
        current_count = db.query(Participation).filter(
            Participation.activity_id == activity_id,
            Participation.status.in_([ParticipationStatus.REGISTERED, ParticipationStatus.CONFIRMED])
        ).count()
        
        if current_count >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")
    
    # Create participation
    participation = Participation(
        activity_id=activity_id,
        user_id=current_user.id,
        status=ParticipationStatus.REGISTERED,
        payment_status=PaymentStatus.NOT_REQUIRED  # TODO: check if club is paid
    )
    
    db.add(participation)
    db.commit()
    
    return {"message": "Successfully joined activity", "activity_id": activity_id}


@app.post("/api/activities/{activity_id}/leave", status_code=200)
async def leave_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Leave an activity"""
    participation = db.query(Participation).filter(
        Participation.activity_id == activity_id,
        Participation.user_id == current_user.id
    ).first()
    
    if not participation:
        raise HTTPException(status_code=404, detail="Not joined this activity")
    
    db.delete(participation)
    db.commit()
    
    return {"message": "Successfully left activity", "activity_id": activity_id}


@app.get("/api/activities/{activity_id}/participants", response_model=List[ParticipantResponse])
async def get_participants(
    activity_id: int,
    db: Session = Depends(get_db)
):
    """Get list of participants for an activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    participations = db.query(Participation, User).join(
        User, Participation.user_id == User.id
    ).filter(
        Participation.activity_id == activity_id
    ).all()
    
    result = []
    for participation, user in participations:
        # Create display name from first_name or username
        display_name = user.first_name or user.username or f"User {user.telegram_id}"

        result.append(ParticipantResponse(
            user_id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            name=display_name,
            status=participation.status,
            attended=participation.attended,
            registered_at=participation.registered_at
        ))

    return result

# ============================================================================
# Groups & Clubs API
# ============================================================================

from groups_clubs_api import (
    # Models
    ClubCreate, ClubUpdate, ClubResponse,
    GroupCreate, GroupUpdate, GroupResponse,
    MembershipUpdate, MemberResponse,
    # Clubs endpoints
    create_club_endpoint, list_clubs_endpoint, get_club_endpoint,
    update_club_endpoint, delete_club_endpoint,
    # Groups endpoints
    create_group_endpoint, list_groups_endpoint, get_group_endpoint,
    update_group_endpoint, delete_group_endpoint,
    # Membership endpoints
    join_club_endpoint, join_group_endpoint,
    get_club_members_endpoint, get_group_members_endpoint,
    update_member_role_endpoint
)

# Clubs
@app.post("/api/clubs", response_model=ClubResponse, status_code=201)
async def create_club(
    club_data: ClubCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new club"""
    return create_club_endpoint(club_data, current_user, db)

@app.get("/api/clubs", response_model=List[ClubResponse])
async def list_clubs(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """List all clubs"""
    return list_clubs_endpoint(limit, offset, current_user, db)

@app.get("/api/clubs/{club_id}", response_model=ClubResponse)
async def get_club(
    club_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get club details"""
    return get_club_endpoint(club_id, current_user, db)

@app.patch("/api/clubs/{club_id}", response_model=ClubResponse)
async def update_club(
    club_id: int,
    club_data: ClubUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update club"""
    return update_club_endpoint(club_id, club_data, current_user, db)

@app.delete("/api/clubs/{club_id}", status_code=204)
async def delete_club(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete club"""
    return delete_club_endpoint(club_id, current_user, db)

@app.post("/api/clubs/{club_id}/join", status_code=201)
async def join_club(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a club"""
    return join_club_endpoint(club_id, current_user, db)

@app.get("/api/clubs/{club_id}/members", response_model=List[MemberResponse])
async def get_club_members(
    club_id: int,
    db: Session = Depends(get_db)
):
    """Get club members"""
    return get_club_members_endpoint(club_id, db)

@app.patch("/api/clubs/{club_id}/members/{user_id}")
async def update_member_role(
    club_id: int,
    user_id: int,
    role_data: MembershipUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update member role"""
    return update_member_role_endpoint(club_id, user_id, role_data, current_user, db)

# Groups
@app.post("/api/groups", response_model=GroupResponse, status_code=201)
async def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new group"""
    return create_group_endpoint(group_data, current_user, db)

@app.get("/api/groups", response_model=List[GroupResponse])
async def list_groups(
    club_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """List groups"""
    return list_groups_endpoint(club_id, limit, offset, current_user, db)

@app.get("/api/groups/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get group details"""
    return get_group_endpoint(group_id, current_user, db)

@app.patch("/api/groups/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: int,
    group_data: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update group"""
    return update_group_endpoint(group_id, group_data, current_user, db)

@app.delete("/api/groups/{group_id}", status_code=204)
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete group"""
    return delete_group_endpoint(group_id, current_user, db)

@app.post("/api/groups/{group_id}/join", status_code=201)
async def join_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a group"""
    return join_group_endpoint(group_id, current_user, db)

@app.get("/api/groups/{group_id}/members", response_model=List[MemberResponse])
async def get_group_members(
    group_id: int,
    db: Session = Depends(get_db)
):
    """Get group members"""
    return get_group_members_endpoint(group_id, db)

# ============================================================================
# Server Startup
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    print(f"Starting Ayda Run API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
