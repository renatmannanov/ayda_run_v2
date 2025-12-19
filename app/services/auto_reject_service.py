"""
Auto-Reject Service

Background service that automatically rejects expired join requests.
Runs every 5 minutes to check for:
1. Activity join requests where activity date has passed
2. Join requests with explicit expires_at timestamp
"""

import logging
import asyncio
from datetime import datetime
from typing import List

from telegram import Bot
from sqlalchemy.orm import Session

from storage.db import SessionLocal, JoinRequest, JoinRequestStatus, User, Activity
from storage.join_request_storage import JoinRequestStorage
from bot.join_request_notifications import send_expiry_notification
from config import settings

logger = logging.getLogger(__name__)


class AutoRejectService:
    """
    Service to automatically reject expired join requests.

    Runs as a background task and checks for expired requests every 5 minutes.
    """

    def __init__(self, bot: Bot, check_interval: int = 300):
        """
        Initialize auto-reject service.

        Args:
            bot: Telegram Bot instance
            check_interval: Check interval in seconds (default: 300 = 5 minutes)
        """
        self.bot = bot
        self.check_interval = check_interval
        self._task = None
        self._running = False

    async def start(self):
        """Start the auto-reject service"""
        if self._running:
            logger.warning("Auto-reject service is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Auto-reject service started (check interval: {self.check_interval}s)")

    async def stop(self):
        """Stop the auto-reject service"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Auto-reject service stopped")

    async def _run(self):
        """Main service loop"""
        while self._running:
            try:
                await self._check_and_reject_expired_requests()
            except Exception as e:
                logger.error(f"Error in auto-reject service: {e}", exc_info=True)

            # Wait for next check
            await asyncio.sleep(self.check_interval)

    async def _check_and_reject_expired_requests(self):
        """Check for expired requests and reject them"""
        session = SessionLocal()

        try:
            jr_storage = JoinRequestStorage(session=session)

            # First, set expires_at for activity join requests where activity date has passed
            marked_count = jr_storage.set_expiry_for_past_activities()
            if marked_count > 0:
                logger.info(f"Marked {marked_count} activity join requests for expiry")

            # Get all expired requests
            expired_requests = jr_storage.get_expired_requests()

            if not expired_requests:
                logger.debug("No expired join requests found")
                return

            logger.info(f"Found {len(expired_requests)} expired join requests")

            # Process each expired request
            for request in expired_requests:
                try:
                    await self._reject_expired_request(session, jr_storage, request)
                except Exception as e:
                    logger.error(f"Error rejecting request {request.id}: {e}", exc_info=True)

            session.commit()
            logger.info(f"Successfully rejected {len(expired_requests)} expired requests")

        except Exception as e:
            logger.error(f"Error checking expired requests: {e}", exc_info=True)
            session.rollback()

        finally:
            session.close()

    async def _reject_expired_request(
        self,
        session: Session,
        jr_storage: JoinRequestStorage,
        request: JoinRequest
    ):
        """
        Reject a single expired request and notify user.

        Args:
            session: Database session
            jr_storage: JoinRequestStorage instance
            request: JoinRequest to reject
        """
        # Update request status to EXPIRED
        jr_storage.update_request_status(request.id, JoinRequestStatus.EXPIRED)

        # Get user
        user = session.query(User).filter(User.id == request.user_id).first()
        if not user or not user.telegram_id:
            logger.warning(f"User {request.user_id} not found or has no telegram_id")
            return

        # Get entity name
        entity_name = "Unknown"
        entity_type = "activity"  # Most common case

        if request.activity_id:
            activity = session.query(Activity).filter(Activity.id == request.activity_id).first()
            if activity:
                entity_name = activity.title
                entity_type = "activity"

        # Send expiry notification to user
        try:
            await send_expiry_notification(
                self.bot,
                user.telegram_id,
                entity_name,
                entity_type
            )
            logger.info(f"Sent expiry notification to user {user.id} for {entity_type} {entity_name}")
        except Exception as e:
            logger.error(f"Failed to send expiry notification to user {user.id}: {e}")


# Singleton instance
_auto_reject_service: AutoRejectService = None


def get_auto_reject_service(bot: Bot = None) -> AutoRejectService:
    """
    Get or create auto-reject service instance.

    Args:
        bot: Telegram Bot instance (required on first call)

    Returns:
        AutoRejectService instance
    """
    global _auto_reject_service

    if _auto_reject_service is None:
        if bot is None:
            raise ValueError("Bot instance required for first call")
        _auto_reject_service = AutoRejectService(bot)

    return _auto_reject_service
