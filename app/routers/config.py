"""
Config API Router - provides public configuration for frontend
"""
from fastapi import APIRouter
from config import settings

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("")
def get_config():
    """
    Get public configuration for frontend.

    Returns bot_username and other public settings needed by webapp.
    """
    return {
        "bot_username": settings.bot_username,
    }
