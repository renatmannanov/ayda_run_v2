"""
Media API Router

Handles photo retrieval from Telegram
"""

from fastapi import APIRouter, HTTPException, Response
from telegram import Bot
from config import settings
import logging
import httpx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/media", tags=["media"])

# Simple in-memory cache for photo URLs (file_id -> fresh_url)
# URLs are valid for 1 hour, we cache for 30 minutes to be safe
_url_cache: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 30 * 60  # 30 minutes


@router.get("/photo/{file_id:path}")
async def get_photo(file_id: str):
    """
    Get photo by Telegram file_id

    Fetches fresh URL from Telegram API and proxies the image content.
    This avoids CORS issues with direct Telegram URLs.
    """
    import time

    try:
        # Check cache first
        cached = _url_cache.get(file_id)
        if cached:
            url, cached_at = cached
            if time.time() - cached_at < _CACHE_TTL:
                telegram_url = url
            else:
                # Cache expired, fetch new URL
                del _url_cache[file_id]
                telegram_url = None
        else:
            telegram_url = None

        # Fetch fresh URL if not cached
        if not telegram_url:
            bot = Bot(token=settings.bot_token)
            file = await bot.get_file(file_id)
            # file.file_path may be full URL or relative path depending on library version
            if file.file_path.startswith("http"):
                telegram_url = file.file_path
            else:
                telegram_url = f"https://api.telegram.org/file/bot{settings.bot_token}/{file.file_path}"
            _url_cache[file_id] = (telegram_url, time.time())

        # Proxy the image content to avoid CORS issues
        async with httpx.AsyncClient() as client:
            response = await client.get(telegram_url, timeout=10.0)

            if response.status_code != 200:
                raise HTTPException(status_code=404, detail="Photo not found on Telegram")

            # Return image with proper content type
            content_type = response.headers.get("content-type", "image/jpeg")
            return Response(
                content=response.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=3600",  # Browser cache for 1 hour
                }
            )

    except httpx.RequestError as e:
        logger.error(f"Error fetching photo {file_id}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch photo from Telegram")
    except Exception as e:
        logger.error(f"Error getting photo {file_id}: {e}")
        raise HTTPException(status_code=404, detail="Photo not found")
