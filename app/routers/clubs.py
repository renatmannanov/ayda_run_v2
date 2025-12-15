"""
Clubs API Router
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from storage.db import Club, Group, Membership, User
from app.core.dependencies import get_db, get_current_user
from permissions import require_club_permission, can_manage_club
from schemas.common import UserRole
from schemas.club import ClubCreate, ClubUpdate, ClubResponse

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


@router.patch("/{club_id}", response_model=ClubResponse)
def update_club(
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


@router.delete("/{club_id}", status_code=204)
def delete_club(
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
