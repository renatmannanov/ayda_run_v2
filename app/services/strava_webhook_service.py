"""
Strava Webhook Retry Service

Background service that:
1. Retries failed Strava API calls (StravaWebhookEvent with result="pending_retry")
2. Cleans up expired PendingStravaMatch records (>24h)

Runs every 5 minutes.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from telegram import Bot
from sqlalchemy.orm import Session

from storage.db import SessionLocal, StravaWebhookEvent, PendingStravaMatch
from app.services.strava_matching_service import process_strava_activity, MAX_RETRY_COUNT

logger = logging.getLogger(__name__)


class StravaWebhookRetryService:
    """Background service for Strava webhook retries and cleanup."""

    def __init__(self, bot: Bot, check_interval: int = 300):
        self.bot = bot
        self.check_interval = check_interval
        self._task = None
        self._running = False

    async def start(self):
        if self._running:
            logger.warning("Strava webhook retry service is already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Strava webhook retry service started (interval: {self.check_interval}s)")

    async def stop(self):
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Strava webhook retry service stopped")

    async def _run(self):
        while self._running:
            try:
                await self._retry_pending()
                await self._cleanup_expired_matches()
            except Exception as e:
                logger.error(f"Error in strava webhook retry service: {e}", exc_info=True)

            await asyncio.sleep(self.check_interval)

    async def _retry_pending(self):
        """Retry failed Strava API calls and recover stuck 'processing' events."""
        db = SessionLocal()
        try:
            now = datetime.utcnow()

            # Recover events stuck in "processing" for >10 minutes
            stuck_cutoff = now - timedelta(minutes=10)
            stuck = db.query(StravaWebhookEvent).filter(
                StravaWebhookEvent.result == "processing",
                StravaWebhookEvent.processed_at < stuck_cutoff
            ).all()
            for event in stuck:
                event.result = "pending_retry"
                event.retry_count = (event.retry_count or 0)
                event.next_retry_at = now  # Retry immediately
                logger.warning(f"Recovered stuck event {event.id} (strava_activity={event.strava_activity_id})")
            if stuck:
                db.commit()

            # Mark events that exceeded max retries as failed
            exhausted = db.query(StravaWebhookEvent).filter(
                StravaWebhookEvent.result == "pending_retry",
                StravaWebhookEvent.retry_count >= MAX_RETRY_COUNT
            ).all()
            for event in exhausted:
                event.result = "error"
                event.processed_at = now
                logger.warning(f"Event {event.id} exceeded max retries ({MAX_RETRY_COUNT}), marking as error")
            if exhausted:
                db.commit()

            pending = db.query(StravaWebhookEvent).filter(
                StravaWebhookEvent.result == "pending_retry",
                StravaWebhookEvent.next_retry_at < now,
                StravaWebhookEvent.retry_count < MAX_RETRY_COUNT
            ).all()

            if not pending:
                return

            logger.info(f"Retrying {len(pending)} pending Strava webhook events")

            for event in pending:
                from storage.db import User
                user = db.query(User).filter(
                    User.strava_athlete_id == event.strava_athlete_id
                ).first()

                if not user:
                    event.result = "error"
                    event.processed_at = now
                    continue

                # Process in a separate task to avoid blocking
                await process_strava_activity(
                    bot=self.bot,
                    user_id=user.id,
                    strava_activity_id=event.strava_activity_id,
                    webhook_event_id=event.id
                )

            db.commit()

        except Exception as e:
            logger.error(f"Error retrying pending events: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    async def _cleanup_expired_matches(self):
        """Remove expired PendingStravaMatch records (>24h)."""
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            expired = db.query(PendingStravaMatch).filter(
                PendingStravaMatch.expires_at < now
            ).all()

            if expired:
                count = len(expired)
                for match in expired:
                    db.delete(match)
                db.commit()
                logger.info(f"Cleaned up {count} expired PendingStravaMatch records")

        except Exception as e:
            logger.error(f"Error cleaning up expired matches: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()


# Singleton
_strava_webhook_retry_service: Optional[StravaWebhookRetryService] = None


def get_strava_webhook_retry_service(bot: Bot = None) -> StravaWebhookRetryService:
    global _strava_webhook_retry_service
    if _strava_webhook_retry_service is None:
        if bot is None:
            raise ValueError("Bot instance required for first call")
        _strava_webhook_retry_service = StravaWebhookRetryService(bot)
    return _strava_webhook_retry_service
