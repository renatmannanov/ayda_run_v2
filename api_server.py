"""
API Server - FastAPI Backend for Ayda Run

Provides REST API for:
- Activities (CRUD)
- Participation (join/leave)
- Static file serving for webapp
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
import logging

from storage.db import init_db, Activity, Participation, User
from app.core.dependencies import get_db, get_current_user, get_current_user_optional
from permissions import can_create_activity_in_club, can_create_activity_in_group, require_activity_owner
from config import settings

# Logger setup (needed before lifespan)
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    init_db()
    logger.info("[SUCCESS] Database initialized")
    yield
    # Shutdown (if needed in future)

app = FastAPI(
    title="Ayda Run API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "PUT"],
    allow_headers=["Content-Type", "X-Telegram-Init-Data"],
    max_age=600,
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

# ============================================================================
# Schemas
# ============================================================================
from schemas.common import (
    SportType, Difficulty, ActivityVisibility, ActivityStatus,
    ParticipationStatus, PaymentStatus, UserRole
)
from schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse
from schemas.club import ClubCreate, ClubUpdate, ClubResponse
from schemas.group import (
    GroupCreate, GroupUpdate, GroupResponse,
    MembershipUpdate, MemberResponse
)
from schemas.user import UserResponse, ParticipantResponse

# Import time and middleware for logging
import time
from starlette.middleware.base import BaseHTTPMiddleware

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests"""

    async def dispatch(self, request, call_next):
        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            process_time = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(process_time * 1000, 2)
                }
            )

            return response

        except Exception as e:
            # Log error
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# ============================================================================
# Include Routers
# ============================================================================
from app.routers import activities

app.include_router(activities.router)

class OnboardingData(BaseModel):
    """Request model for completing onboarding"""
    preferred_sports: Optional[list[str]] = None  # e.g., ["running", "trail"]



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

# UserResponse imported from schemas

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

# Activities API moved to app/routers/activities.py

# ============================================================================
# Groups & Clubs API
# ============================================================================

from groups_clubs_api import (
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
    logger.info(f"Starting Ayda Run API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
