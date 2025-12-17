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
from schemas.group import MemberResponse

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
# Membership API
# ============================================================================

@router.post("/{club_id}/join", status_code=201)
def join_club(
    club_id: str,
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
            role=membership.role,
            joined_at=membership.joined_at.isoformat() if membership.joined_at else None
        ))

    return result


# ============================================================================
