"""
Users API Router
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional

from storage.db import User
from storage.user_storage import UserStorage
from app.core.dependencies import get_db, get_current_user
from schemas.user import UserResponse, UserProfileUpdate

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
    Update current user profile (photo, strava_link)

    - photo: Telegram file_id or URL to user avatar
    - strava_link: URL to user's Strava profile
    """
    user_storage = UserStorage(session=db)

    # Update profile
    updated_user = user_storage.update_profile(
        user_id=current_user.id,
        photo=profile_data.photo,
        strava_link=profile_data.strava_link
    )

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(updated_user)
