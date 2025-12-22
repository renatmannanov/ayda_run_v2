"""
GPX File Service

Handles GPX file validation, upload to Telegram channel, and download.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException

from telegram import Bot, InputFile
from config import settings

logger = logging.getLogger(__name__)


class GPXService:
    """Service for handling GPX file operations."""

    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
    ALLOWED_EXTENSIONS = ['.gpx']

    @staticmethod
    async def validate_gpx(file: UploadFile) -> bytes:
        """
        Validate GPX file and return contents.

        Args:
            file: Uploaded file

        Returns:
            File content as bytes

        Raises:
            HTTPException: If validation fails
        """
        # 1. Check extension
        filename = file.filename or ""
        if not filename.lower().endswith('.gpx'):
            raise HTTPException(
                status_code=400,
                detail="Only .gpx files are allowed"
            )

        # 2. Read content
        content = await file.read()

        # 3. Check size
        if len(content) > GPXService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 20MB"
            )

        # 4. Check if empty
        if len(content) == 0:
            raise HTTPException(
                status_code=400,
                detail="File is empty"
            )

        # 5. Validate XML structure
        try:
            root = ET.fromstring(content)

            # Check for GPX namespace or tag
            tag_lower = root.tag.lower()
            if 'gpx' not in tag_lower:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid GPX file: root element must be 'gpx'"
                )

        except ET.ParseError as e:
            logger.warning(f"GPX XML parse error: {e}")
            raise HTTPException(
                status_code=400,
                detail="Invalid GPX file: not a valid XML format"
            )

        logger.info(f"GPX file validated: {filename}, size: {len(content)} bytes")
        return content

    @staticmethod
    async def upload_to_telegram(
        bot: Bot,
        content: bytes,
        filename: str,
        activity_title: str,
        activity_id: str
    ) -> Tuple[str, int]:
        """
        Upload GPX file to Telegram channel.

        Args:
            bot: Telegram Bot instance
            content: File content as bytes
            filename: Original filename
            activity_title: Activity title for caption
            activity_id: Activity ID for reference

        Returns:
            Tuple of (file_id, message_id)
        """
        # Create caption with activity info
        caption = (
            f"GPX: {activity_title}\n"
            f"Activity ID: {activity_id}\n"
            f"Uploaded: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        # Send to channel
        try:
            message = await bot.send_document(
                chat_id=settings.gpx_channel_id,
                document=InputFile(content, filename=filename),
                caption=caption
            )

            file_id = message.document.file_id
            message_id = message.message_id

            logger.info(
                f"GPX uploaded to Telegram: file_id={file_id}, "
                f"message_id={message_id}, activity={activity_id}"
            )

            return file_id, message_id

        except Exception as e:
            logger.error(f"Failed to upload GPX to Telegram: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to upload GPX file. Please try again."
            )

    @staticmethod
    async def get_file_url(bot: Bot, file_id: str) -> str:
        """
        Get download URL for a file from Telegram.

        Args:
            bot: Telegram Bot instance
            file_id: Telegram file_id

        Returns:
            Download URL
        """
        try:
            file = await bot.get_file(file_id)
            return file.file_path
        except Exception as e:
            logger.error(f"Failed to get file URL from Telegram: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve GPX file"
            )

    @staticmethod
    async def delete_from_telegram(
        bot: Bot,
        message_id: int
    ) -> bool:
        """
        Delete GPX file message from Telegram channel.

        Args:
            bot: Telegram Bot instance
            message_id: Message ID in the channel

        Returns:
            True if deleted successfully
        """
        try:
            await bot.delete_message(
                chat_id=settings.gpx_channel_id,
                message_id=message_id
            )
            logger.info(f"GPX message deleted: message_id={message_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete GPX message: {e}")
            return False
