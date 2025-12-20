"""
Groups API Router
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from storage.db import Club, Group, Membership, User, JoinRequest, JoinRequestStatus
from app.core.dependencies import get_db, get_current_user
from permissions import require_group_permission, require_club_permission
from schemas.common import UserRole
from schemas.group import GroupCreate, GroupUpdate, GroupResponse, MembershipUpdate, MemberResponse
from schemas.join_request import JoinRequestCreate, JoinRequestResponse
from storage.join_request_storage import JoinRequestStorage

# Bot notifications
from bot.join_request_notifications import send_join_request_to_organizer
from telegram import Bot
from config import settings
import asyncio

router = APIRouter(prefix="/api/groups", tags=["groups"])


@router.post("", response_model=GroupResponse, status_code=201)
def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GroupResponse:
    """
    Create a new group
    
    - Standalone group: anyone can create
    - Club group: requires organizer permission in that club
    """
    # Check permissions if creating group within club
    if group_data.club_id:
        require_club_permission(db, current_user, group_data.club_id, UserRole.ORGANIZER)

    # Create group
    from app_config.constants import DEFAULT_COUNTRY
    group_dict = group_data.model_dump()

    # Set defaults from user profile if not provided
    if not group_dict.get('city'):
        group_dict['city'] = current_user.city
    if not group_dict.get('country'):
        group_dict['country'] = DEFAULT_COUNTRY

    group = Group(**group_dict, creator_id=current_user.id)
    
    db.add(group)
    db.commit()
    db.refresh(group)
    
    # Add creator as admin/trainer
    # If club group - trainer, if standalone - admin
    role = UserRole.TRAINER if group_data.club_id else UserRole.ADMIN
    membership = Membership(
        user_id=current_user.id,
        group_id=group.id,
        role=role
    )
    db.add(membership)
    db.commit()
    
    # Convert to response
    response = GroupResponse.model_validate(group)
    response.members_count = 1
    response.is_member = True
    response.user_role = role
    
    return response


@router.get("", response_model=List[GroupResponse])
def list_groups(
    club_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[GroupResponse]:
    """List groups, optionally filtered by club"""
    query = db.query(Group)
    
    if club_id is not None:
        query = query.filter(Group.club_id == club_id)
    
    # Eager load club to get name efficiently
    query = query.options(joinedload(Group.club))
    
    groups = query.offset(offset).limit(limit).all()
    
    result = []
    for group in groups:
        response = GroupResponse.model_validate(group)
        
        # Count members
        response.members_count = db.query(Membership).filter(Membership.group_id == group.id).count()
        
        # Check if current user is member
        if current_user:
            membership = db.query(Membership).filter(
                Membership.group_id == group.id,
                Membership.user_id == current_user.id
            ).first()
            response.is_member = membership is not None
            response.user_role = membership.role if membership else None
        
        if group.club:
            response.club_name = group.club.name

        result.append(response)
    
    return result


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GroupResponse:
    """Get group details"""
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Convert to response
    response = GroupResponse.model_validate(group)
    response.members_count = db.query(Membership).filter(Membership.group_id == group.id).count()
    
    if current_user:
        membership = db.query(Membership).filter(
            Membership.group_id == group.id,
            Membership.user_id == current_user.id
        ).first()
        response.is_member = membership is not None
        response.user_role = membership.role if membership else None
    
    if group.club:
        response.club_name = group.club.name

    return response


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: str,
    group_data: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> GroupResponse:
    """Update group (trainer or higher)"""
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check permissions
    require_group_permission(db, current_user, group_id, UserRole.TRAINER)
    
    # Update fields
    update_data = group_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)
    
    db.commit()
    db.refresh(group)
    
    # Convert to response
    response = GroupResponse.model_validate(group)
    response.members_count = db.query(Membership).filter(Membership.group_id == group.id).count()
    
    membership = db.query(Membership).filter(
        Membership.group_id == group.id,
        Membership.user_id == current_user.id
    ).first()
    response.is_member = True
    response.user_role = membership.role
    
    return response


@router.delete("/{group_id}", status_code=204)
def delete_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete group (admin only for standalone, organizer+ for club groups)"""
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check permissions based on group type
    if group.club_id:
        # Club group - organizer can delete
        require_club_permission(db, current_user, group.club_id, UserRole.ORGANIZER)
    else:
        # Standalone group - admin only
        require_group_permission(db, current_user, group_id, UserRole.ADMIN)
    
    db.delete(group)
    db.commit()
    
    return None


# ============================================================================
# Membership API
# ============================================================================

@router.post("/{group_id}/join", status_code=201)
def join_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a group (for closed groups, use request-join endpoint)"""
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if not group.is_open:
        raise HTTPException(
            status_code=403,
            detail="This group is closed. Please send a join request instead using POST /api/groups/{group_id}/request-join"
        )
    
    # Check if already member
    existing = db.query(Membership).filter(
        Membership.group_id == group_id,
        Membership.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Already a member of this group")
    
    # Add membership
    membership = Membership(
        user_id=current_user.id,
        group_id=group_id,
        role=UserRole.MEMBER
    )
    
    db.add(membership)
    db.commit()
    
    return {"message": "Successfully joined group", "group_id": group_id}


@router.get("/{group_id}/members", response_model=List[MemberResponse])
def get_group_members(
    group_id: str,
    db: Session = Depends(get_db)
) -> List[MemberResponse]:
    """Get list of group members"""
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    memberships = db.query(Membership, User).join(
        User, Membership.user_id == User.id
    ).filter(
        Membership.group_id == group_id
    ).all()
    
    result = []
    for membership, user in memberships:
        # Create display name from first_name or username
        display_name = user.first_name or user.username or f"User {user.telegram_id}"

        result.append(MemberResponse(
            user_id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            name=display_name,
            role=membership.role,
            joined_at=membership.joined_at.isoformat() if membership.joined_at else None,
            preferred_sports=user.preferred_sports
        ))

    return result


def update_member_role_endpoint(
    club_id: int,
    user_id: int,
    role_data: MembershipUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update member role in club (admin only)"""
    # Check permissions
    require_club_permission(db, current_user, club_id, UserRole.ADMIN)
    
    # Find membership
    membership = db.query(Membership).filter(
        Membership.club_id == club_id,
        Membership.user_id == user_id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    
    membership.role = role_data.role
    db.commit()

    return {"message": "Role updated successfully"}


# ============================================================================
# Join Requests API (for closed groups)
# ============================================================================

@router.post("/{group_id}/request-join", status_code=201)
def request_join_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a join request for a closed group"""
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check if group is open
    if group.is_open:
        raise HTTPException(
            status_code=400,
            detail="This group is open. Please use POST /api/groups/{group_id}/join instead"
        )

    # Check if already member
    existing_membership = db.query(Membership).filter(
        Membership.group_id == group_id,
        Membership.user_id == current_user.id
    ).first()

    if existing_membership:
        raise HTTPException(status_code=400, detail="Already a member of this group")

    # Check if pending request already exists
    jr_storage = JoinRequestStorage(session=db)
    existing_request = jr_storage.get_user_pending_request(current_user.id, "group", group_id)

    if existing_request:
        raise HTTPException(status_code=400, detail="You already have a pending join request for this group")

    # Create join request
    join_request = jr_storage.create_join_request(current_user.id, "group", group_id)

    if not join_request:
        raise HTTPException(status_code=500, detail="Failed to create join request")

    # Send notification to group organizer via bot
    try:
        # Get group creator (organizer)
        creator = db.query(User).filter(User.id == group.creator_id).first()

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
                'name': group.name,
                'type': 'group',
                'id': group.id
            }

            # Send notification synchronously
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
        "group_id": group_id
    }


@router.get("/{group_id}/join-requests", response_model=List[JoinRequestResponse])
def get_group_join_requests(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending join requests for a group (trainers/organizers only)"""
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check permissions (trainer or higher)
    require_group_permission(db, current_user, group_id, UserRole.TRAINER)

    # Get pending requests
    jr_storage = JoinRequestStorage(session=db)
    requests = jr_storage.get_pending_requests_for_entity("group", group_id)

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
            group_id=request.group_id,
            status=request.status.value,
            expires_at=request.expires_at,
            user_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
            username=user.username,
            user_first_name=user.first_name,
            user_sports=user.preferred_sports,
            user_strava_link=getattr(user, 'strava_link', None),
            entity_name=group.name,
            entity_type="group"
        ))

    return result


@router.post("/{group_id}/join-requests/{request_id}/approve", status_code=200)
def approve_group_join_request(
    group_id: str,
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve a join request and add user to group (trainers/organizers only)"""
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check permissions
    require_group_permission(db, current_user, group_id, UserRole.TRAINER)

    # Get join request
    jr_storage = JoinRequestStorage(session=db)
    join_request = jr_storage.get_join_request(request_id)

    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")

    if join_request.group_id != group_id:
        raise HTTPException(status_code=400, detail="Join request does not belong to this group")

    if join_request.status != JoinRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Join request already {join_request.status.value}")

    # Add user to group
    membership = Membership(
        user_id=join_request.user_id,
        group_id=group_id,
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


@router.post("/{group_id}/join-requests/{request_id}/reject", status_code=200)
def reject_group_join_request(
    group_id: str,
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject a join request (trainers/organizers only)"""
    group = db.query(Group).filter(Group.id == group_id).first()

    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Check permissions
    require_group_permission(db, current_user, group_id, UserRole.TRAINER)

    # Get join request
    jr_storage = JoinRequestStorage(session=db)
    join_request = jr_storage.get_join_request(request_id)

    if not join_request:
        raise HTTPException(status_code=404, detail="Join request not found")

    if join_request.group_id != group_id:
        raise HTTPException(status_code=400, detail="Join request does not belong to this group")

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
