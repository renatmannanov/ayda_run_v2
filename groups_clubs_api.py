"""
Groups & Clubs API endpoints

This module contains API endpoints for:
- Creating and managing clubs
- Creating and managing groups (standalone and club-attached)
- Membership management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from storage.db import (
    get_db, Club, Group, Membership, User
)
from sqlalchemy.orm import joinedload
from auth import get_current_user
from permissions import (
    can_manage_club, can_manage_group,
    require_club_permission, require_group_permission
)

# ============================================================================
# Schemas
# ============================================================================
from schemas.common import UserRole
from schemas.club import ClubCreate, ClubUpdate, ClubResponse
from schemas.group import (
    GroupCreate, GroupUpdate, GroupResponse,
    MembershipUpdate, MemberResponse
)


# ============================================================================
# Clubs API
# ============================================================================

def create_club_endpoint(
    club_data: ClubCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ClubResponse:
    """
    Create a new club
    
    Anyone can create a club and becomes its admin automatically
    """
    # Create club
    club = Club(
        **club_data.model_dump(),
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


def list_clubs_endpoint(
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


def get_club_endpoint(
    club_id: int,
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


def update_club_endpoint(
    club_id: int,
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


def delete_club_endpoint(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete club (admin only)"""
    club = db.query(Club).filter(Club.id == club_id).first()
    
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    # Check permissions (admin only)
    require_club_permission(db, current_user, club_id, UserRole.ADMIN)
    
    db.delete(club)
    db.commit()
    
    return None


# ============================================================================
# Groups API
# ============================================================================

def create_group_endpoint(
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
    group = Group(**group_data.model_dump())
    
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


def list_groups_endpoint(
    club_id: Optional[int] = None,
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


def get_group_endpoint(
    group_id: int,
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


def update_group_endpoint(
    group_id: int,
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


def delete_group_endpoint(
    group_id: int,
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

def join_club_endpoint(
    club_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Join a club (for invite-only clubs, use invite endpoint)"""
    club = db.query(Club).filter(Club.id == club_id).first()
    
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
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


def join_group_endpoint(
    group_id: int,
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


def get_club_members_endpoint(
    club_id: int,
    db: Session = Depends(get_db)
) -> List[MemberResponse]:
    """Get list of club members"""
    club = db.query(Club).filter(Club.id == club_id).first()
    
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")
    
    memberships = db.query(Membership, User).join(
        User, Membership.user_id == User.id
    ).filter(
        Membership.club_id == club_id
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
            joined_at=membership.joined_at
        ))

    return result


def get_group_members_endpoint(
    group_id: int,
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
            joined_at=membership.joined_at
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
