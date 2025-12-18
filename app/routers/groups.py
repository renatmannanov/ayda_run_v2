"""
Groups API Router
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from storage.db import Club, Group, Membership, User
from app.core.dependencies import get_db, get_current_user
from permissions import require_group_permission, require_club_permission
from schemas.common import UserRole
from schemas.group import GroupCreate, GroupUpdate, GroupResponse, MembershipUpdate, MemberResponse

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

    group = Group(**group_dict)
    
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
    """Join a group (only if is_open=True)"""
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if not group.is_open:
        raise HTTPException(status_code=403, detail="This group is invite-only")
    
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
