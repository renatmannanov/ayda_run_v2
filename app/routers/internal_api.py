"""
Internal API for cross-service communication.

Protected by shared API key (X-API-Key header).
Used by gpx_predictor to fetch Strava tokens and OAuth URLs.
"""

import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.strava_service import StravaService
from config import settings
from storage.db import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/internal", tags=["internal"])


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify shared API key for service-to-service calls."""
    if not settings.cross_service_api_key:
        raise HTTPException(status_code=503, detail="Internal API not configured")
    if x_api_key != settings.cross_service_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@router.get("/strava/token")
async def get_strava_token(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """
    Return a valid (refreshed if needed) Strava access token for a user.

    Used by gpx_predictor to make Strava API calls on behalf of users
    who authorized through ayda_run's OAuth.
    """
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.strava_athlete_id:
        raise HTTPException(status_code=404, detail="Strava not connected")

    strava_service = StravaService(db)
    access_token = await strava_service.get_valid_token(user)
    if not access_token:
        raise HTTPException(status_code=404, detail="Could not obtain valid Strava token")

    return {
        "access_token": access_token,
        "athlete_id": user.strava_athlete_id,
        "scope": "read,activity:read_all",
    }


@router.get("/strava/auth")
async def get_strava_auth_url(
    telegram_id: int = Query(..., description="User's Telegram ID"),
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """
    Generate a Strava OAuth URL for an external service user.

    Lazy-creates the user by telegram_id if they don't exist in ayda_run.
    Returns the OAuth URL even if Strava is already connected (allows re-auth).
    """
    base_url = (settings.base_url or "").rstrip("/")
    if not base_url:
        raise HTTPException(status_code=503, detail="BASE_URL not configured")

    if not settings.strava_client_id:
        raise HTTPException(status_code=503, detail="Strava integration not configured")

    # Lazy create user by telegram_id
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Created user for external OAuth: telegram_id=%s, user_id=%s", telegram_id, user.id)

    # Generate Strava OAuth URL (same callback as native ayda_run flow)
    callback_url = f"{base_url}/api/strava/callback"
    params = urlencode({
        "client_id": settings.strava_client_id,
        "redirect_uri": callback_url,
        "response_type": "code",
        "scope": "read,activity:read_all",
        "state": user.id,
    })

    auth_url = f"https://www.strava.com/oauth/authorize?{params}"

    return {
        "auth_url": auth_url,
        "already_connected": user.strava_athlete_id is not None,
    }
