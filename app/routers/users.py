"""
Users API Router
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from storage.db import User
from storage.user_storage import UserStorage
from app.core.dependencies import get_db, get_current_user
from schemas.user import UserResponse, UserProfileUpdate, UserDetailedStatsResponse, UserCountsResponse
from permissions import get_user_entity_counts

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Get current user profile
    """
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Update current user profile (photo, strava_link, show_photo)

    - photo: Telegram file_id or URL to user avatar
    - strava_link: URL to user's Strava profile
    - show_photo: Show photo instead of initials in avatar
    """
    user_storage = UserStorage(session=db)

    # Update profile
    updated_user = user_storage.update_profile(
        user_id=current_user.id,
        photo=profile_data.photo,
        strava_link=profile_data.strava_link,
        show_photo=profile_data.show_photo
    )

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(updated_user)


@router.get("/me/stats", response_model=UserDetailedStatsResponse)
def get_user_stats(
    period: str = Query("month", description="Period: month, quarter, year, all"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserDetailedStatsResponse:
    """
    Get detailed user statistics for period.

    - period: Time period for stats (month, quarter, year, all)
    """
    user_storage = UserStorage(session=db)
    stats = user_storage.get_detailed_stats(
        user_id=current_user.id,
        period=period
    )
    return UserDetailedStatsResponse(**stats)


@router.get("/me/counts", response_model=UserCountsResponse)
def get_user_counts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserCountsResponse:
    """
    Get current entity counts and limits for the user.

    Returns counts of:
    - clubs: created by user
    - groups: created by user
    - activities_upcoming: upcoming activities created by user
    """
    counts = get_user_entity_counts(db, current_user.id)
    return UserCountsResponse(**counts)
