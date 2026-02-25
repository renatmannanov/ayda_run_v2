"""
Internal API for cross-service communication.

Protected by shared API key (X-API-Key header).
Used by gpx_predictor to fetch Strava tokens.
"""

import logging
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
