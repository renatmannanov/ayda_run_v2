"""
Media API Router

Handles photo retrieval from Telegram
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse
from telegram import Bot
from config import settings
import logging
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/media", tags=["media"])


@router.get("/photo/{file_id:path}")
async def get_photo(file_id: str):
    """
    Get photo by Telegram file_id

    Returns redirect to Telegram CDN URL
    """
    try:
        bot = Bot(token=settings.bot_token)

        # Get file from Telegram
        file = await bot.get_file(file_id)

        # Construct full URL to Telegram file
        # file.file_path is relative, need to construct full URL
        telegram_url = f"https://api.telegram.org/file/bot{settings.bot_token}/{file.file_path}"

        # Redirect to Telegram CDN URL (more efficient)
        return RedirectResponse(url=telegram_url)

    except Exception as e:
        logger.error(f"Error getting photo {file_id}: {e}")
        raise HTTPException(status_code=404, detail="Photo not found")
