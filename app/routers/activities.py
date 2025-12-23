"""
Activities API Router

Handles all activity-related endpoints:
- CRUD operations for activities
- Participation (join/leave)
- Participants list
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
import httpx
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from storage.db import Activity, Participation, User, Membership, JoinRequest, JoinRequestStatus, Club, Group
from app.core.dependencies import get_db, get_current_user, get_current_user_optional
from permissions import can_create_activity_in_club, can_create_activity_in_group, require_activity_owner
from schemas.common import SportType, Difficulty, ActivityVisibility, ActivityStatus, ParticipationStatus, PaymentStatus
from schemas.activity import ActivityCreate, ActivityUpdate, ActivityResponse
from schemas.user import ParticipantResponse
from schemas.join_request import JoinRequestCreate, JoinRequestResponse
from storage.join_request_storage import JoinRequestStorage
from config import settings

# Bot notifications
from bot.join_request_notifications import send_join_request_to_organizer
from bot.activity_notifications import (
    send_new_activity_notification_to_user,
    send_new_activity_notification_to_group,
    send_activity_cancelled_notification,
    send_activity_updated_notification
)
from telegram import Bot
import asyncio

# GPX service
from app.services.gpx_service import GPXService

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

    # Automatically add creator as participant
    creator_participation = Participation(
        activity_id=activity.id,
        user_id=current_user.id,
        status=ParticipationStatus.CONFIRMED
    )
    db.add(creator_participation)
    db.commit()

    # Send notifications to club/group members (async, don't block response)
    asyncio.create_task(_send_new_activity_notifications(
        activity_id=activity.id,
        activity_title=activity.title,
        activity_date=activity.date,
        location=activity.location or "Не указано",
        club_id=activity.club_id,
        group_id=activity.group_id,
        max_participants=activity.max_participants
    ))

    # Convert to response
    response = ActivityResponse.model_validate(activity)
    response.participants_count = 1  # Creator is already a participant
    response.is_joined = True
    response.is_creator = True

    return response


@router.get("", response_model=List[ActivityResponse])
async def list_activities(
    club_id: Optional[str] = Query(None),
    group_id: Optional[str] = Query(None),
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
    query = query.options(joinedload(Activity.club), joinedload(Activity.group), joinedload(Activity.creator))

    # Pagination
    activities = query.offset(offset).limit(limit).all()

    # Convert to response with participant counts
    result = []
    logger.debug(f"Processing {len(activities)} activities")
    for activity in activities:
        response = ActivityResponse.model_validate(activity)
        response.participants_count = db.query(Participation).filter(
            Participation.activity_id == activity.id,
            Participation.status.in_([
                ParticipationStatus.REGISTERED,
                ParticipationStatus.CONFIRMED,
                ParticipationStatus.AWAITING,
                ParticipationStatus.ATTENDED
            ])
        ).count()

        if current_user:
            participation = db.query(Participation).filter(
                Participation.activity_id == activity.id,
                Participation.user_id == current_user.id
            ).first()
            response.is_joined = participation is not None
            if participation:
                # Show awaiting status "on the fly" if activity has passed
                # This ensures UI shows correct state even before background service runs
                if (participation.status in [ParticipationStatus.REGISTERED, ParticipationStatus.CONFIRMED]
                    and activity.date < datetime.now()):
                    response.participation_status = ParticipationStatus.AWAITING
                else:
                    response.participation_status = participation.status

        # Populate names (eager loaded now)
        if activity.club:
            response.club_name = activity.club.name
            logger.debug(f"Activity {activity.id}: Set club_name='{activity.club.name}'")
        if activity.group:
            response.group_name = activity.group.name
            logger.debug(f"Activity {activity.id}: Set group_name='{activity.group.name}'")
        if activity.creator:
            # Build display name from first_name + last_name
            creator = activity.creator
            response.creator_name = f"{creator.first_name or ''} {creator.last_name or ''}".strip() or creator.username or "Аноним"

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

    # GPX info
    response.has_gpx = bool(activity.gpx_file_id)

    if current_user:
        participation = db.query(Participation).filter(
            Participation.activity_id == activity.id,
            Participation.user_id == current_user.id
        ).first()
        response.is_joined = participation is not None
        response.is_creator = activity.creator_id == current_user.id
        if participation:
            # Show awaiting status "on the fly" if activity has passed
            # This ensures UI shows correct state even before background service runs
            if (participation.status in [ParticipationStatus.REGISTERED, ParticipationStatus.CONFIRMED]
                and activity.date < datetime.now()):
                response.participation_status = ParticipationStatus.AWAITING
            else:
                response.participation_status = participation.status

    # Populate names
    if activity.club:
        response.club_name = activity.club.name
    if activity.group:
        response.group_name = activity.group.name
    if activity.creator:
        # Build display name from first_name + last_name
        creator = activity.creator
        response.creator_name = f"{creator.first_name or ''} {creator.last_name or ''}".strip() or creator.username or "Аноним"

    return response


@router.patch("/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: str,
    activity_data: ActivityUpdate,
    notify_participants: bool = Query(False, description="Send notifications to participants about changes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update activity (only creator can update, only future activities)"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check permissions
    require_activity_owner(current_user, activity)

    # Check if activity is in the past
    if activity.date < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot update past activities")

    # Save old values for change summary
    old_values = {
        'title': activity.title,
        'date': activity.date,
        'location': activity.location,
        'distance': activity.distance,
        'duration': activity.duration,
        'max_participants': activity.max_participants
    }

    # Update fields
    update_data = activity_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(activity, field, value)

    db.commit()
    db.refresh(activity)

    # Send notifications to participants if requested
    if notify_participants:
        changes_summary = _build_changes_summary(old_values, activity)
        if changes_summary:
            asyncio.create_task(_send_activity_updated_notifications(
                activity_id=activity.id,
                activity_title=activity.title,
                changes_summary=changes_summary,
                current_user_id=current_user.id
            ))

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
    notify_participants: bool = Query(False, description="Send notifications to participants about cancellation"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete activity (only creator can delete, only future activities)"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check permissions
    require_activity_owner(current_user, activity)

    # Check if activity is in the past
    if activity.date < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot delete past activities")

    # Get participants to notify BEFORE deleting
    participants_to_notify = []
    if notify_participants:
        participations = db.query(Participation, User).join(
            User, Participation.user_id == User.id
        ).filter(
            Participation.activity_id == activity_id,
            Participation.status.in_([ParticipationStatus.REGISTERED, ParticipationStatus.CONFIRMED]),
            User.id != current_user.id  # Don't notify the creator
        ).all()
        participants_to_notify = [(p.status, u) for p, u in participations if u.telegram_id]

    # Save activity data for notifications
    activity_data = {
        'title': activity.title,
        'date': activity.date,
        'location': activity.location or "Не указано",
        'organizer_name': current_user.first_name or current_user.username or "Организатор"
    }

    db.delete(activity)
    db.commit()

    # Send notifications asynchronously
    if participants_to_notify:
        asyncio.create_task(_send_activity_cancelled_notifications(
            participants_to_notify,
            activity_data
        ))

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
    """Join an activity (for closed activities, use request-join endpoint)"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check if activity is open
    if not activity.is_open:
        raise HTTPException(
            status_code=403,
            detail="This activity is closed. Please send a join request instead using POST /api/activities/{activity_id}/request-join"
        )

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
            Participation.status.in_([
                ParticipationStatus.REGISTERED,
                ParticipationStatus.CONFIRMED,
                ParticipationStatus.AWAITING,
                ParticipationStatus.ATTENDED
            ])
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


@router.post("/{activity_id}/confirm", status_code=200)
async def confirm_attendance(
    activity_id: str,
    attended: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm attendance for a past activity.

    Called when user confirms whether they attended or missed the activity.
    Only works for participations in 'awaiting' status.

    Args:
        activity_id: Activity ID
        attended: True if user attended, False if missed

    Returns:
        New participation status (attended or missed)
    """
    # Get participation
    participation = db.query(Participation).filter(
        Participation.activity_id == activity_id,
        Participation.user_id == current_user.id
    ).first()

    if not participation:
        raise HTTPException(status_code=404, detail="You are not registered for this activity")

    # Check if participation is in awaiting status (or REGISTERED/CONFIRMED for past activities)
    # We allow confirmation for REGISTERED/CONFIRMED because UI shows them as "awaiting" after activity ends
    allowed_statuses = [
        ParticipationStatus.AWAITING,
        ParticipationStatus.REGISTERED,
        ParticipationStatus.CONFIRMED
    ]
    if participation.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm attendance. Current status: {participation.status.value}"
        )

    # Verify activity has actually ended (can only confirm past activities)
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if activity and activity.date > datetime.now():
        raise HTTPException(
            status_code=400,
            detail="Cannot confirm attendance for future activities"
        )

    # Update status based on attendance
    if attended:
        participation.status = ParticipationStatus.ATTENDED
        participation.attended = True
    else:
        participation.status = ParticipationStatus.MISSED
        participation.attended = False

    db.commit()

    new_status = "attended" if attended else "missed"
    logger.info(f"User {current_user.id} confirmed {new_status} for activity {activity_id}")

    return {
        "message": f"Attendance confirmed: {new_status}",
        "status": new_status,
        "activity_id": activity_id
    }


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
            registered_at=participation.registered_at,
            preferred_sports=user.preferred_sports,
            photo=user.photo,
            strava_link=user.strava_link,
            is_organizer=(str(user.id) == str(activity.creator_id))
        ))

    return result


# ============================================================================
# Join Requests API (for closed activities)
# ============================================================================

@router.post("/{activity_id}/request-join", status_code=201)
async def request_join_activity(
    activity_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a join request for a closed activity"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check if activity is open
    if activity.is_open:
        raise HTTPException(
            status_code=400,
            detail="This activity is open. Please use POST /api/activities/{activity_id}/join instead"
        )

    # Check if already joined
    existing_participation = db.query(Participation).filter(
        Participation.activity_id == activity_id,
        Participation.user_id == current_user.id
    ).first()

    if existing_participation:
        raise HTTPException(status_code=400, detail="Already joined this activity")

    # Check if pending request already exists
    jr_storage = JoinRequestStorage(session=db)
    existing_request = jr_storage.get_user_pending_request(current_user.id, "activity", activity_id)

    if existing_request:
        raise HTTPException(status_code=400, detail="You already have a pending join request for this activity")

    # Create join request
    join_request = jr_storage.create_join_request(current_user.id, "activity", activity_id)

    if not join_request:
        raise HTTPException(status_code=500, detail="Failed to create join request")

    # Set expiry to activity date
    join_request.expires_at = activity.date
    db.commit()

    # Send notification to activity creator via bot
    try:
        # Get activity creator
        creator = db.query(User).filter(User.id == activity.creator_id).first()

        if creator and creator.telegram_id:
            # Prepare user data
            user_data = {
                'first_name': current_user.first_name or 'Unknown',
                'username': current_user.username,
                'preferred_sports': current_user.preferred_sports or '',
                'strava_link': getattr(current_user, 'strava_link', '')
            }

            # Prepare entity data
            entity_data = {
                'name': activity.title,
                'type': 'activity',
                'id': activity.id
            }

            # Send notification asynchronously
            bot = Bot(token=settings.bot_token)
            await send_join_request_to_organizer(
                bot,
                creator.telegram_id,
                user_data,
                entity_data,
                join_request.id
            )
    except Exception as e:
        # Log error but don't fail the request
        logger.error(f"Failed to send join request notification: {e}")

    return {
        "message": "Join request sent successfully",
        "request_id": join_request.id,
        "activity_id": activity_id
    }


@router.get("/{activity_id}/join-requests", response_model=List[JoinRequestResponse])
async def get_activity_join_requests(
    activity_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending join requests for an activity (creator only)"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check permissions (only creator can see requests)
    require_activity_owner(current_user, activity)

    # Get pending requests
    jr_storage = JoinRequestStorage(session=db)
    requests = jr_storage.get_pending_requests_for_entity("activity", activity_id)

    # Build response with user info
    result = []
    for request in requests:
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            continue

        result.append(JoinRequestResponse(
            id=request.id,
            created_at=request.created_at,
            user_id=request.user_id,
            activity_id=request.activity_id,
            status=request.status.value,
            expires_at=request.expires_at,
            user_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
            username=user.username,
            user_first_name=user.first_name,
            user_sports=user.preferred_sports,
            user_strava_link=getattr(user, 'strava_link', None),
            entity_name=activity.title,
            entity_type="activity"
        ))

    return result


@router.post("/{activity_id}/join-requests/{request_id}/approve", status_code=200)
async def approve_activity_join_request(
    activity_id: str,
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a join request and add user to activity (creator only)"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check permissions
    require_activity_owner(current_user, activity)

    # Get join request
    jr_storage = JoinRequestStorage(session=db)
    join_request = jr_storage.get_join_request(request_id)

    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")

    if join_request.activity_id != activity_id:
        raise HTTPException(status_code=400, detail="Join request does not belong to this activity")

    if join_request.status != JoinRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Join request already {join_request.status.value}")

    # Check max participants
    if activity.max_participants:
        current_count = db.query(Participation).filter(
            Participation.activity_id == activity_id,
            Participation.status.in_([
                ParticipationStatus.REGISTERED,
                ParticipationStatus.CONFIRMED,
                ParticipationStatus.AWAITING,
                ParticipationStatus.ATTENDED
            ])
        ).count()

        if current_count >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

    # Add user to activity
    participation = Participation(
        activity_id=activity_id,
        user_id=join_request.user_id,
        status=ParticipationStatus.REGISTERED,
        payment_status=PaymentStatus.NOT_REQUIRED
    )
    db.add(participation)

    # Update request status
    jr_storage.update_request_status(request_id, JoinRequestStatus.APPROVED)

    db.commit()

    # TODO: Send approval notification to user via bot (Phase 5)

    return {
        "message": "Join request approved successfully",
        "request_id": request_id,
        "user_id": join_request.user_id
    }


@router.post("/{activity_id}/join-requests/{request_id}/reject", status_code=200)
async def reject_activity_join_request(
    activity_id: str,
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a join request (creator only)"""
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Check permissions
    require_activity_owner(current_user, activity)

    # Get join request
    jr_storage = JoinRequestStorage(session=db)
    join_request = jr_storage.get_join_request(request_id)

    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")

    if join_request.activity_id != activity_id:
        raise HTTPException(status_code=400, detail="Join request does not belong to this activity")

    if join_request.status != JoinRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Join request already {join_request.status.value}")

    # Update request status
    jr_storage.update_request_status(request_id, JoinRequestStatus.REJECTED)

    db.commit()

    # TODO: Send rejection notification to user via bot (Phase 5)

    return {
        "message": "Join request rejected successfully",
        "request_id": request_id,
        "user_id": join_request.user_id
    }


# ============================================================================
# GPX File Management
# ============================================================================

@router.post("/{activity_id}/gpx", status_code=201)
async def upload_gpx(
    activity_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload GPX file for an activity.
    Only the activity creator can upload GPX files.
    """
    # 1. Get activity
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # 2. Check permissions (only creator can upload)
    if activity.creator_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only activity creator can upload GPX files"
        )

    # 3. Check if GPX already exists
    if activity.gpx_file_id:
        raise HTTPException(
            status_code=400,
            detail="GPX file already exists. Delete it first to upload a new one."
        )

    # 4. Validate GPX file
    content = await GPXService.validate_gpx(file)

    # 5. Upload to Telegram channel
    bot = Bot(token=settings.bot_token)
    file_id, message_id = await GPXService.upload_to_telegram(
        bot=bot,
        content=content,
        filename=file.filename or "route.gpx",
        activity_title=activity.title,
        activity_id=activity.id
    )

    # 6. Update activity in database
    activity.gpx_file_id = file_id
    activity.gpx_filename = file.filename or "route.gpx"
    activity.gpx_file_message_id = message_id

    db.commit()

    logger.info(f"GPX uploaded for activity {activity_id}: {file.filename}")

    return {
        "success": True,
        "filename": activity.gpx_filename,
        "message": "GPX file uploaded successfully"
    }


@router.get("/{activity_id}/gpx")
async def download_gpx(
    activity_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Download GPX file for an activity.
    Permission check based on activity visibility and user membership.
    """
    # 1. Get activity
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # 2. Check if GPX exists
    if not activity.gpx_file_id:
        raise HTTPException(status_code=404, detail="No GPX file for this activity")

    # 3. Check permissions
    can_download = _check_gpx_permission(activity, current_user, db)
    if not can_download:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to download this GPX file"
        )

    # 4. Get file URL from Telegram
    bot = Bot(token=settings.bot_token)
    file_url = await GPXService.get_file_url(bot, activity.gpx_file_id)

    # 5. Download file from Telegram and stream to client
    async with httpx.AsyncClient() as client:
        response = await client.get(file_url)

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail="Failed to download GPX file from storage"
            )

        # Return file as streaming response
        return StreamingResponse(
            iter([response.content]),
            media_type="application/gpx+xml",
            headers={
                "Content-Disposition": f'attachment; filename="{activity.gpx_filename or "route.gpx"}"'
            }
        )


def _check_gpx_permission(activity: Activity, user: Optional[User], db: Session) -> bool:
    """
    Check if user can download GPX file.

    Rules:
    - Creator always can
    - Participants always can
    - For open activities - anyone can
    - For club activities - club members can
    - For group activities - group members can
    """
    # No user = check if activity is public/open
    if not user:
        return activity.is_open or activity.visibility == ActivityVisibility.PUBLIC

    # Creator always can
    if activity.creator_id == user.id:
        return True

    # Check if user is participant
    participation = db.query(Participation).filter(
        Participation.activity_id == activity.id,
        Participation.user_id == user.id
    ).first()
    if participation:
        return True

    # For open activities - anyone can
    if activity.is_open:
        return True

    # For club activities - club members can
    if activity.club_id:
        membership = db.query(Membership).filter(
            Membership.club_id == activity.club_id,
            Membership.user_id == user.id
        ).first()
        if membership:
            return True

    # For group activities - group members can
    if activity.group_id:
        membership = db.query(Membership).filter(
            Membership.group_id == activity.group_id,
            Membership.user_id == user.id
        ).first()
        if membership:
            return True

    return False


@router.delete("/{activity_id}/gpx", status_code=200)
async def delete_gpx(
    activity_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete GPX file from an activity.
    Only the activity creator can delete GPX files.
    """
    # 1. Get activity
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # 2. Check permissions
    if activity.creator_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only activity creator can delete GPX files"
        )

    # 3. Check if GPX exists
    if not activity.gpx_file_id:
        raise HTTPException(status_code=404, detail="No GPX file to delete")

    # 4. Delete from Telegram channel (optional, don't fail if it fails)
    if activity.gpx_file_message_id:
        bot = Bot(token=settings.bot_token)
        await GPXService.delete_from_telegram(bot, activity.gpx_file_message_id)

    # 5. Clear GPX fields in database
    old_filename = activity.gpx_filename
    activity.gpx_file_id = None
    activity.gpx_filename = None
    activity.gpx_file_message_id = None

    db.commit()

    logger.info(f"GPX deleted from activity {activity_id}: {old_filename}")

    return {
        "success": True,
        "message": "GPX file deleted successfully"
    }


# ============================================================================
# Helper Functions for Notifications
# ============================================================================

async def _send_new_activity_notifications(
    activity_id: str,
    activity_title: str,
    activity_date,
    location: str,
    club_id: Optional[str],
    group_id: Optional[str],
    max_participants: Optional[int]
) -> None:
    """
    Send new activity notifications to club/group members.
    Runs asynchronously in background.

    Args:
        activity_id: Activity ID
        activity_title: Activity title
        activity_date: Activity date/time
        location: Activity location
        club_id: Club ID (if club activity)
        group_id: Group ID (if group activity)
        max_participants: Maximum participants
    """
    try:
        from storage.db import SessionLocal
        session = SessionLocal()

        try:
            # Get entity (club or group)
            entity = None
            entity_name = "Активность"
            telegram_group_id = None

            if club_id:
                entity = session.query(Club).filter(Club.id == club_id).first()
                if entity:
                    entity_name = entity.name
                    telegram_group_id = entity.telegram_chat_id
            elif group_id:
                entity = session.query(Group).filter(Group.id == group_id).first()
                if entity:
                    entity_name = entity.name
                    telegram_group_id = entity.telegram_chat_id

            # Get all members of the club/group
            members = []
            if club_id:
                memberships = session.query(Membership).filter(Membership.club_id == club_id).all()
                members = [session.query(User).filter(User.id == m.user_id).first() for m in memberships]
            elif group_id:
                memberships = session.query(Membership).filter(Membership.group_id == group_id).all()
                members = [session.query(User).filter(User.id == m.user_id).first() for m in memberships]

            # Filter out None values
            members = [m for m in members if m and m.telegram_id]

            # Build webapp link (Telegram deep link)
            webapp_link = f"https://t.me/{settings.bot_username}?start=activity_{activity_id}"

            # Initialize bot
            bot = Bot(token=settings.bot_token)

            # Send to each member's personal chat
            for member in members:
                try:
                    await send_new_activity_notification_to_user(
                        bot=bot,
                        user_telegram_id=member.telegram_id,
                        activity_title=activity_title,
                        activity_date=activity_date,
                        location=location,
                        participants_count=0,
                        max_participants=max_participants,
                        entity_name=entity_name,
                        webapp_link=webapp_link
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification to user {member.telegram_id}: {e}")

            # Send to Telegram group if linked
            if telegram_group_id:
                try:
                    await send_new_activity_notification_to_group(
                        bot=bot,
                        group_chat_id=telegram_group_id,
                        activity_title=activity_title,
                        activity_date=activity_date,
                        location=location,
                        webapp_link=webapp_link
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification to group {telegram_group_id}: {e}")

            logger.info(f"Sent new activity notifications for activity {activity_id} to {len(members)} members")

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in _send_new_activity_notifications: {e}", exc_info=True)


async def _send_activity_cancelled_notifications(
    participants: list,
    activity_data: dict
) -> None:
    """
    Send cancellation notifications to participants.
    Runs asynchronously in background.

    Args:
        participants: List of (participation_status, user) tuples
        activity_data: Dict with title, date, location, organizer_name
    """
    try:
        bot = Bot(token=settings.bot_token)

        for _, user in participants:
            try:
                await send_activity_cancelled_notification(
                    bot=bot,
                    user_telegram_id=user.telegram_id,
                    activity_title=activity_data['title'],
                    activity_date=activity_data['date'],
                    location=activity_data['location'],
                    organizer_name=activity_data['organizer_name']
                )
            except Exception as e:
                logger.error(f"Failed to send cancellation notification to user {user.telegram_id}: {e}")

        logger.info(f"Sent cancellation notifications to {len(participants)} participants")

    except Exception as e:
        logger.error(f"Error in _send_activity_cancelled_notifications: {e}", exc_info=True)


async def _send_activity_updated_notifications(
    activity_id: str,
    activity_title: str,
    changes_summary: str,
    current_user_id: str
) -> None:
    """
    Send update notifications to participants.
    Runs asynchronously in background.

    Args:
        activity_id: Activity ID
        activity_title: Activity title
        changes_summary: Human-readable summary of changes
        current_user_id: ID of user who made changes (to exclude from notifications)
    """
    try:
        from storage.db import SessionLocal
        session = SessionLocal()

        try:
            # Get participants
            participations = session.query(Participation, User).join(
                User, Participation.user_id == User.id
            ).filter(
                Participation.activity_id == activity_id,
                Participation.status.in_([ParticipationStatus.REGISTERED, ParticipationStatus.CONFIRMED]),
                User.id != current_user_id
            ).all()

            participants = [(p, u) for p, u in participations if u.telegram_id]

            # Build webapp link
            webapp_link = f"https://t.me/{settings.bot_username}?start=activity_{activity_id}"

            bot = Bot(token=settings.bot_token)

            for _, user in participants:
                try:
                    await send_activity_updated_notification(
                        bot=bot,
                        user_telegram_id=user.telegram_id,
                        activity_title=activity_title,
                        changes_summary=changes_summary,
                        webapp_link=webapp_link
                    )
                except Exception as e:
                    logger.error(f"Failed to send update notification to user {user.telegram_id}: {e}")

            logger.info(f"Sent update notifications for activity {activity_id} to {len(participants)} participants")

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Error in _send_activity_updated_notifications: {e}", exc_info=True)


def _build_changes_summary(old_values: dict, activity) -> str:
    """
    Build human-readable summary of changes.

    Args:
        old_values: Dict with old field values
        activity: Updated activity object

    Returns:
        String with changes summary, or empty string if no changes
    """
    changes = []

    if old_values.get('title') != activity.title:
        changes.append(f"• Название: {activity.title}")

    if old_values.get('date') != activity.date:
        date_str = activity.date.strftime("%d %B в %H:%M")
        changes.append(f"• Дата: {date_str}")

    if old_values.get('location') != activity.location:
        changes.append(f"• Место: {activity.location}")

    if old_values.get('distance') != activity.distance:
        if activity.distance:
            changes.append(f"• Дистанция: {activity.distance} км")

    if old_values.get('duration') != activity.duration:
        if activity.duration:
            changes.append(f"• Длительность: {activity.duration} мин")

    if old_values.get('max_participants') != activity.max_participants:
        if activity.max_participants:
            changes.append(f"• Макс. участников: {activity.max_participants}")

    return "\n".join(changes)
