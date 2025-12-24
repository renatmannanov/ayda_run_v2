"""
Clubs API Router
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from storage.db import Club, Group, Membership, User, JoinRequest, JoinRequestStatus, Activity, MembershipStatus
from app.core.dependencies import get_db, get_current_user
from permissions import require_club_permission, can_manage_club
from schemas.common import UserRole, ActivityVisibility
from schemas.club import ClubCreate, ClubUpdate, ClubResponse
from schemas.group import MemberResponse
from schemas.join_request import JoinRequestCreate, JoinRequestResponse
from storage.join_request_storage import JoinRequestStorage

# Bot notifications
from bot.join_request_notifications import send_join_request_to_organizer
from bot.club_group_notifications import send_club_deleted_notification
from telegram import Bot
from config import settings
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clubs", tags=["clubs"])


@router.post("", response_model=ClubResponse, status_code=201)
def create_club(
    club_data: ClubCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ClubResponse:
    """
    Create a new club

    Anyone can create a club and becomes its admin automatically
    """
    # Create club
    from app_config.constants import DEFAULT_COUNTRY
    club_dict = club_data.model_dump()

    # Set defaults from user profile if not provided
    if not club_dict.get('city'):
        club_dict['city'] = current_user.city
    if not club_dict.get('country'):
        club_dict['country'] = DEFAULT_COUNTRY

    club = Club(
        **club_dict,
        creator_id=current_user.id
    )
    
    db.add(club)
    db.commit()
    db.refresh(club)
    
    # Add creator as admin
    membership = Membership(
        user_id=current_user.id,
        club_id=club.id,
        role=UserRole.ADMIN
    )
    db.add(membership)
    db.commit()
    
    # Convert to response
    response = ClubResponse.model_validate(club)
    response.groups_count = 0
    response.members_count = 1
    response.is_member = True
    response.user_role = UserRole.ADMIN
    
    return response


@router.get("", response_model=List[ClubResponse])
def list_clubs(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[ClubResponse]:
    """List all clubs (public for now)"""
    clubs = db.query(Club).offset(offset).limit(limit).all()
    
    result = []
    for club in clubs:
        response = ClubResponse.model_validate(club)
        
        # Count groups
        response.groups_count = db.query(Group).filter(Group.club_id == club.id).count()
        
        # Count members
        response.members_count = db.query(Membership).filter(Membership.club_id == club.id).count()
        
        # Check if current user is member
        if current_user:
            membership = db.query(Membership).filter(
                Membership.club_id == club.id,
                Membership.user_id == current_user.id
            ).first()
            response.is_member = membership is not None
            response.user_role = membership.role if membership else None
        
        result.append(response)
    
    return result


@router.get("/{club_id}", response_model=ClubResponse)
def get_club(
    club_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ClubResponse:
    """Get club details"""
    club = db.query(Club).filter(Club.id == club_id).first()
    
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Convert to response
    response = ClubResponse.model_validate(club)
    response.groups_count = db.query(Group).filter(Group.club_id == club.id).count()
    response.members_count = db.query(Membership).filter(Membership.club_id == club.id).count()

    if current_user:
        membership = db.query(Membership).filter(
            Membership.club_id == club.id,
            Membership.user_id == current_user.id
        ).first()
        response.is_member = membership is not None
        response.user_role = membership.role if membership else None

    return response


@router.patch("/{club_id}", response_model=ClubResponse)
def update_club(
    club_id: str,
    club_data: ClubUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ClubResponse:
    """Update club (organizer or admin only)"""
    club = db.query(Club).filter(Club.id == club_id).first()
    
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check permissions
    require_club_permission(db, current_user, club_id, UserRole.ORGANIZER)
    
    # Update fields
    update_data = club_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(club, field, value)
    
    db.commit()
    db.refresh(club)
    
    # Convert to response
    response = ClubResponse.model_validate(club)
    response.groups_count = db.query(Group).filter(Group.club_id == club.id).count()
    response.members_count = db.query(Membership).filter(Membership.club_id == club.id).count()
    
    membership = db.query(Membership).filter(
        Membership.club_id == club.id,
        Membership.user_id == current_user.id
    ).first()
    response.is_member = True
    response.user_role = membership.role
    
    return response


@router.delete("/{club_id}", status_code=204)
def delete_club(
    club_id: str,
    notify_members: bool = Query(False, description="Send notification to all members"),
    delete_activities: bool = Query(True, description="Delete activities or detach to creators"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete club (admin only)

    Args:
        notify_members: If True, send Telegram notification to all club members
        delete_activities: If True, delete all club activities. If False, detach activities to their creators
    """
    club = db.query(Club).filter(Club.id == club_id).first()

    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Check permissions (admin only)
    require_club_permission(db, current_user, club_id, UserRole.ADMIN)

    # Store data for notifications before deletion
    club_name = club.name
    admin_name = current_user.first_name or current_user.username or "Admin"

    # Get members to notify (excluding current user)
    members_to_notify = []
    if notify_members:
        memberships = db.query(Membership).filter(
            Membership.club_id == club_id,
            Membership.user_id != current_user.id
        ).all()

        for membership in memberships:
            user = db.query(User).filter(User.id == membership.user_id).first()
            if user and user.telegram_id:
                members_to_notify.append(user.telegram_id)

    # Handle activities
    if delete_activities:
        # Activities will be cascade-deleted with the club
        pass
    else:
        # Detach activities - set club_id to NULL (keep creator ownership)
        db.query(Activity).filter(Activity.club_id == club_id).update(
            {Activity.club_id: None},
            synchronize_session=False
        )

    # Delete club (cascades to groups, memberships)
    db.delete(club)
    db.commit()

    # Send notifications asynchronously
    if members_to_notify:
        try:
            bot = Bot(token=settings.bot_token)
            loop = asyncio.new_event_loop()
            try:
                for telegram_id in members_to_notify:
                    loop.run_until_complete(
                        send_club_deleted_notification(
                            bot,
                            telegram_id,
                            club_name,
                            admin_name,
                            activities_deleted=delete_activities
                        )
                    )
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Failed to send club deletion notifications: {e}")

    return None


# ============================================================================
# Membership API
# ============================================================================

@router.post("/{club_id}/join", status_code=201)
def join_club(
    club_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a club (for closed clubs, use request-join endpoint)"""
    club = db.query(Club).filter(Club.id == club_id).first()

    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Check if club is open
    if not club.is_open:
        raise HTTPException(
            status_code=403,
            detail="This club is closed. Please send a join request instead using POST /api/clubs/{club_id}/request-join"
        )

    # Check if already member
    existing = db.query(Membership).filter(
        Membership.club_id == club_id,
        Membership.user_id == current_user.id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already a member of this club")

    # Add membership
    membership = Membership(
        user_id=current_user.id,
        club_id=club_id,
        role=UserRole.MEMBER
    )

    db.add(membership)
    db.commit()

    return {"message": "Successfully joined club", "club_id": club_id}


@router.get("/{club_id}/members", response_model=List[MemberResponse])
def get_club_members(
    club_id: str,
    db: Session = Depends(get_db)
):
    """Get list of club members"""
    club = db.query(Club).filter(Club.id == club_id).first()

    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Get all memberships
    memberships = db.query(Membership).filter(
        Membership.club_id == club_id
    ).join(User).all()

    # Build response
    result = []
    for membership in memberships:
        user = membership.user
        result.append(MemberResponse(
            user_id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            name=user.first_name or user.username or f"User {user.telegram_id}",
            photo=user.photo,
            show_photo=user.show_photo,
            role=membership.role,
            joined_at=membership.joined_at.isoformat() if membership.joined_at else None,
            preferred_sports=user.preferred_sports
        ))

    return result


# ============================================================================
# Join Requests API (for closed clubs)
# ============================================================================

@router.post("/{club_id}/request-join", status_code=201)
def request_join_club(
    club_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a join request for a closed club"""
    club = db.query(Club).filter(Club.id == club_id).first()

    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Check if club is open (should use direct join instead)
    if club.is_open:
        raise HTTPException(
            status_code=400,
            detail="This club is open. Please use POST /api/clubs/{club_id}/join instead"
        )

    # Check if already member
    existing_membership = db.query(Membership).filter(
        Membership.club_id == club_id,
        Membership.user_id == current_user.id
    ).first()

    if existing_membership:
        raise HTTPException(status_code=400, detail="Already a member of this club")

    # Check if pending request already exists
    jr_storage = JoinRequestStorage(session=db)
    existing_request = jr_storage.get_user_pending_request(current_user.id, "club", club_id)

    if existing_request:
        raise HTTPException(status_code=400, detail="You already have a pending join request for this club")

    # Create join request
    join_request = jr_storage.create_join_request(current_user.id, "club", club_id)

    if not join_request:
        raise HTTPException(status_code=500, detail="Failed to create join request")

    # Send notification to club organizer via bot
    try:
        # Get club creator (organizer)
        creator = db.query(User).filter(User.id == club.creator_id).first()

        if creator and creator.telegram_id:
            # Prepare user data
            user_data = {
                'first_name': current_user.first_name or 'Unknown',
                'username': current_user.username,
                'preferred_sports': current_user.preferred_sports or '',
                'strava_link': getattr(current_user, 'strava_link', '')  # Will be added in future task
            }

            # Prepare entity data
            entity_data = {
                'name': club.name,
                'type': 'club',
                'id': club.id
            }

            # Send notification synchronously
            import asyncio
            bot = Bot(token=settings.bot_token)
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(
                    send_join_request_to_organizer(
                        bot,
                        creator.telegram_id,
                        user_data,
                        entity_data,
                        join_request.id
                    )
                )
            finally:
                loop.close()
    except Exception as e:
        # Log error but don't fail the request
        import logging
        logging.error(f"Failed to send join request notification: {e}")

    return {
        "message": "Join request sent successfully",
        "request_id": join_request.id,
        "club_id": club_id
    }


@router.get("/{club_id}/join-requests", response_model=List[JoinRequestResponse])
def get_club_join_requests(
    club_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending join requests for a club (organizers only)"""
    club = db.query(Club).filter(Club.id == club_id).first()

    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Check permissions (organizer or admin)
    require_club_permission(db, current_user, club_id, UserRole.ORGANIZER)

    # Get pending requests
    jr_storage = JoinRequestStorage(session=db)
    requests = jr_storage.get_pending_requests_for_entity("club", club_id)

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
            club_id=request.club_id,
            status=request.status.value,
            expires_at=request.expires_at,
            user_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
            username=user.username,
            user_first_name=user.first_name,
            user_sports=user.preferred_sports,
            user_strava_link=getattr(user, 'strava_link', None),
            entity_name=club.name,
            entity_type="club"
        ))

    return result


@router.post("/{club_id}/join-requests/{request_id}/approve", status_code=200)
def approve_club_join_request(
    club_id: str,
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a join request and add user to club (organizers only)"""
    club = db.query(Club).filter(Club.id == club_id).first()

    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Check permissions
    require_club_permission(db, current_user, club_id, UserRole.ORGANIZER)

    # Get join request
    jr_storage = JoinRequestStorage(session=db)
    join_request = jr_storage.get_join_request(request_id)

    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")

    if join_request.club_id != club_id:
        raise HTTPException(status_code=400, detail="Join request does not belong to this club")

    if join_request.status != JoinRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Join request already {join_request.status.value}")

    # Add user to club
    membership = Membership(
        user_id=join_request.user_id,
        club_id=club_id,
        role=UserRole.MEMBER
    )
    db.add(membership)

    # Update request status
    jr_storage.update_request_status(request_id, JoinRequestStatus.APPROVED)

    db.commit()

    # TODO: Send approval notification to user via bot (Phase 5)

    return {
        "message": "Join request approved successfully",
        "request_id": request_id,
        "user_id": join_request.user_id
    }


@router.post("/{club_id}/join-requests/{request_id}/reject", status_code=200)
def reject_club_join_request(
    club_id: str,
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a join request (organizers only)"""
    club = db.query(Club).filter(Club.id == club_id).first()

    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    # Check permissions
    require_club_permission(db, current_user, club_id, UserRole.ORGANIZER)

    # Get join request
    jr_storage = JoinRequestStorage(session=db)
    join_request = jr_storage.get_join_request(request_id)

    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")

    if join_request.club_id != club_id:
        raise HTTPException(status_code=400, detail="Join request does not belong to this club")

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
