"""
Activities API Router

Handles all activity-related endpoints:
- CRUD operations for activities
- Participation (join/leave)
- Participants list
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
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
from bot.activity_notifications import send_new_activity_notification_to_user, send_new_activity_notification_to_group
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
    response.participants_count = 0
    response.is_joined = False

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

    # GPX info
    response.has_gpx = bool(activity.gpx_file_id)

    if current_user:
        participation = db.query(Participation).filter(
            Participation.activity_id == activity.id,
            Participation.user_id == current_user.id
        ).first()
        response.is_joined = participation is not None
        response.is_creator = activity.creator_id == current_user.id

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
            registered_at=participation.registered_at,
            preferred_sports=user.preferred_sports
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
            Participation.status.in_([ParticipationStatus.REGISTERED, ParticipationStatus.CONFIRMED])
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
