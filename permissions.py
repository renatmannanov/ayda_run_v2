"""
Permissions utilities for Ayda Run

This module handles role-based access control for:
- Activities (create, update, delete, mark attendance)
- Clubs (manage, invite)
- Groups (manage, invite)
"""

from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from storage.db import (
    User, Club, Group, Activity, Membership, UserRole
)


def get_user_role_in_club(db: Session, user_id: int, club_id: int) -> Optional[UserRole]:
    """Get user's role in a club"""
    membership = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.club_id == club_id
    ).first()
    return membership.role if membership else None


def get_user_role_in_group(db: Session, user_id: int, group_id: int) -> Optional[UserRole]:
    """Get user's role in a group"""
    membership = db.query(Membership).filter(
        Membership.user_id == user_id,
        Membership.group_id == group_id
    ).first()
    return membership.role if membership else None


def can_create_activity_in_club(db: Session, user: User, club_id: int) -> bool:
    """Check if user can create activity in a club"""
    role = get_user_role_in_club(db, user.id, club_id)
    return role in [UserRole.ADMIN, UserRole.ORGANIZER]


def can_create_activity_in_group(db: Session, user: User, group_id: int) -> bool:
    """
    Check if user can create activity in a group
    
    Rules:
    - Standalone group: any member can create
    - Group within club: only trainer/organizer/admin
    """
    from storage.db import SessionLocal
    session = SessionLocal()
    try:
        group = session.query(Group).filter(Group.id == group_id).first()
        if not group:
            return False
        
        role = get_user_role_in_group(session, user.id, group_id)
        if not role:
            return False
        
        # Standalone group: any member
        if group.club_id is None:
            return True
        
        # Group within club: trainer or higher
        return role in [UserRole.TRAINER, UserRole.ORGANIZER, UserRole.ADMIN]
    finally:
        session.close()


def can_manage_club(db: Session, user: User, club_id: int) -> bool:
    """Check if user can manage a club (organizer or admin)"""
    role = get_user_role_in_club(db, user.id, club_id)
    return role in [UserRole.ADMIN, UserRole.ORGANIZER]


def can_manage_group(db: Session, user: User, group_id: int) -> bool:
    """Check if user can manage a group (trainer or higher)"""
    role = get_user_role_in_group(db, user.id, group_id)
    return role in [UserRole.TRAINER, UserRole.ORGANIZER, UserRole.ADMIN]


def can_mark_attendance(db: Session, user: User, activity: Activity) -> bool:
    """
    Check if user can mark attendance for an activity
    
    Rules:
    - Activity creator can always mark attendance
    - Club/Group organizers can mark attendance
    - Trainers can mark attendance for their group
    """
    # Creator can always mark
    if activity.creator_id == user.id:
        return True
    
    # Check club permissions
    if activity.club_id:
        role = get_user_role_in_club(db, user.id, activity.club_id)
        if role in [UserRole.ADMIN, UserRole.ORGANIZER]:
            return True
    
    # Check group permissions
    if activity.group_id:
        role = get_user_role_in_group(db, user.id, activity.group_id)
        if role in [UserRole.TRAINER, UserRole.ORGANIZER, UserRole.ADMIN]:
            return True
    
    return False


def require_club_permission(db: Session, user: User, club_id: int, min_role: UserRole = UserRole.ORGANIZER):
    """Raise exception if user doesn't have required role in club"""
    role = get_user_role_in_club(db, user.id, club_id)
    
    role_hierarchy = {
        UserRole.MEMBER: 0,
        UserRole.TRAINER: 1,
        UserRole.ORGANIZER: 2,
        UserRole.ADMIN: 3
    }
    
    if not role or role_hierarchy.get(role, 0) < role_hierarchy.get(min_role, 0):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required: {min_role.value}"
        )


def require_group_permission(db: Session, user: User, group_id: int, min_role: UserRole = UserRole.TRAINER):
    """Raise exception if user doesn't have required role in group"""
    role = get_user_role_in_group(db, user.id, group_id)
    
    role_hierarchy = {
        UserRole.MEMBER: 0,
        UserRole.TRAINER: 1,
        UserRole.ORGANIZER: 2,
        UserRole.ADMIN: 3
    }
    
    if not role or role_hierarchy.get(role, 0) < role_hierarchy.get(min_role, 0):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required: {min_role.value}"
        )


def require_activity_owner(user: User, activity: Activity):
    """Raise exception if user is not the activity creator"""
    if activity.creator_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Only activity creator can perform this action"
        )
