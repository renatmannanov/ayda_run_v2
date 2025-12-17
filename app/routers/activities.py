"""
Activities API Router

Handles all activity-related endpoints:
- CRUD operations for activities
- Participation (join/leave)
- Participants list
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from storage.db import Activity, Participation, User
from app.core.dependencies import get_db, get_current_user, get_current_user_optional
from permissions import can_create_activity_in_club, can_create_activity_in_group, require_activity_owner
from schemas.common import SportType, Difficulty, ActivityVisibility, ActivityStatus, ParticipationStatus, PaymentStatus
from schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse
from schemas.user import ParticipantResponse
from config import settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/activities", tags=["activities"])


# ============================================================================
# Activity CRUD
# ============================================================================

@router.post("", response_model=ActivityResponse, status_code=201)
async def create_activity(
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
    from app_config.constants import DEFAULT_COUNTRY

    activity_dict = activity_data.model_dump()
    # Set default country if not provided
    if not activity_dict.get('country'):
        activity_dict['country'] = DEFAULT_COUNTRY

    # Set city from user's profile if not provided (frontend doesn't send it yet)
    if not activity_dict.get('city'):
        activity_dict['city'] = current_user.city

    activity = Activity(
        **activity_dict,
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


@router.get("", response_model=List[ActivityResponse])
async def list_activities(
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
    logger.debug(f"Processing {len(activities)} activities")
    for activity in activities:
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

        # Populate names (eager loaded now)
        if activity.club:
            response.club_name = activity.club.name
            logger.debug(f"Activity {activity.id}: Set club_name='{activity.club.name}'")
        if activity.group:
            response.group_name = activity.group.name
            logger.debug(f"Activity {activity.id}: Set group_name='{activity.group.name}'")

        result.append(response)

    return result


@router.get("/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: str,
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


@router.patch("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: str,
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


@router.delete("/{activity_id}", status_code=204)
async def delete_activity(
    activity_id: str,
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
# Participation
# ============================================================================

@router.post("/{activity_id}/join", status_code=201)
async def join_activity(
    activity_id: str,
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


@router.post("/{activity_id}/leave", status_code=200)
async def leave_activity(
    activity_id: str,
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


@router.get("/{activity_id}/participants", response_model=List[ParticipantResponse])
async def get_participants(
    activity_id: str,
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
