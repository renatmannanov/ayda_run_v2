"""
Awaiting Confirmation Service

Background service that automatically transitions participations to 'awaiting' status
after activity start time has passed.

Runs every 5 minutes to check for:
1. Participations with status 'registered' or 'confirmed'
2. Where activity.date < now()

For each found participation:
1. Update status to 'awaiting'
2. Send Telegram notification asking user to confirm attendance
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Tuple

from telegram import Bot
from sqlalchemy.orm import Session
from sqlalchemy import and_

from storage.db import SessionLocal, Participation, Activity, User, ParticipationStatus
from app.core.timezone import utc_now
from bot.activity_notifications import send_awaiting_confirmation_notification, send_organizer_checkin_notification
from config import settings

logger = logging.getLogger(__name__)


class AwaitingConfirmationService:
    """
    Service to automatically transition participations to 'awaiting' status
    after activity time has passed.

    Runs as a background task and checks every 5 minutes.
    """

    def __init__(self, bot: Bot, check_interval: int = 300):
        """
        Initialize awaiting confirmation service.

        Args:
            bot: Telegram Bot instance
            check_interval: Check interval in seconds (default: 300 = 5 minutes)
        """
        self.bot = bot
        self.check_interval = check_interval
        self._task = None
        self._running = False

    async def start(self):
        """Start the awaiting confirmation service"""
        if self._running:
            logger.warning("Awaiting confirmation service is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Awaiting confirmation service started (check interval: {self.check_interval}s)")

    async def stop(self):
        """Stop the awaiting confirmation service"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Awaiting confirmation service stopped")

    async def _run(self):
        """Main service loop"""
        while self._running:
            try:
                await self._check_and_transition_participations()
            except Exception as e:
                logger.error(f"Error in awaiting confirmation service: {e}", exc_info=True)

            # Wait for next check
            await asyncio.sleep(self.check_interval)

    async def _check_and_transition_participations(self):
        """Check for participations to transition and send notifications"""
        session = SessionLocal()

        try:
            now = utc_now()  # Use UTC time for consistent comparison

            # Find all participations where:
            # - status is REGISTERED or CONFIRMED
            # - activity.date < now (activity has started/passed)
            # - activity is not demo data
            participations_to_update = session.query(Participation).join(
                Activity, Participation.activity_id == Activity.id
            ).filter(
                and_(
                    Participation.status.in_([
                        ParticipationStatus.REGISTERED,
                        ParticipationStatus.CONFIRMED
                    ]),
                    Activity.date < now,
                    Activity.is_demo == False
                )
            ).all()

            if not participations_to_update:
                logger.debug("No participations to transition to awaiting")
                return

            logger.info(f"Found {len(participations_to_update)} participations to transition to awaiting")

            # Group participations by activity for organizer notifications
            activity_participations = {}
            for participation in participations_to_update:
                activity_id = participation.activity_id
                if activity_id not in activity_participations:
                    activity_participations[activity_id] = []
                activity_participations[activity_id].append(participation)

            # Process each participation and send appropriate notifications
            notified_organizers = set()  # Track which organizers we've notified

            for participation in participations_to_update:
                try:
                    await self._transition_to_awaiting(session, participation, notified_organizers)
                except Exception as e:
                    logger.error(f"Error transitioning participation {participation.id}: {e}", exc_info=True)

            session.commit()
            logger.info(f"Successfully transitioned {len(participations_to_update)} participations to awaiting")

        except Exception as e:
            logger.error(f"Error checking participations: {e}", exc_info=True)
            session.rollback()

        finally:
            session.close()

    async def _transition_to_awaiting(
        self,
        session: Session,
        participation: Participation,
        notified_organizers: set
    ):
        """
        Transition a single participation to awaiting and send notification.

        For club/group activities: sends notification only to organizer (once per activity)
        For personal activities: sends notification to participant

        Args:
            session: Database session
            participation: Participation to transition
            notified_organizers: Set of activity IDs for which organizer was already notified
        """
        # Update participation status
        participation.status = ParticipationStatus.AWAITING

        # Get user and activity for notification
        user = session.query(User).filter(User.id == participation.user_id).first()
        activity = session.query(Activity).filter(Activity.id == participation.activity_id).first()

        if not activity:
            logger.warning(f"Activity {participation.activity_id} not found")
            return

        # Check if this is a club/group activity
        is_club_group_activity = activity.club_id or activity.group_id

        if is_club_group_activity:
            # For club/group activities: notify organizer (once per activity)
            activity_key = str(activity.id)
            if activity_key not in notified_organizers:
                await self._notify_organizer(session, activity)
                notified_organizers.add(activity_key)
        else:
            # For personal activities: notify participant
            if not user or not user.telegram_id:
                logger.warning(f"User {participation.user_id} not found or has no telegram_id")
                return

            try:
                await send_awaiting_confirmation_notification(
                    bot=self.bot,
                    user_telegram_id=user.telegram_id,
                    activity_id=activity.id,
                    activity_title=activity.title,
                    activity_date=activity.date,
                    location=activity.location or "Не указано",
                    country=activity.country,
                    city=activity.city
                )
                logger.info(f"Sent awaiting confirmation notification to user {user.id} for activity {activity.id}")
            except Exception as e:
                logger.error(f"Failed to send awaiting confirmation notification to user {user.id}: {e}")

    async def _notify_organizer(self, session: Session, activity: Activity):
        """
        Send checkin notification to activity organizer.

        Args:
            session: Database session
            activity: Activity object
        """
        # Get organizer (creator)
        organizer = session.query(User).filter(User.id == activity.creator_id).first()

        if not organizer or not organizer.telegram_id:
            logger.warning(f"Organizer {activity.creator_id} not found or has no telegram_id")
            return

        # Count participants
        participants_count = session.query(Participation).filter(
            Participation.activity_id == activity.id
        ).count()

        # Build webapp link
        webapp_link = f"https://t.me/{settings.bot_username}?start=activity_{activity.id}"

        try:
            await send_organizer_checkin_notification(
                bot=self.bot,
                organizer_telegram_id=organizer.telegram_id,
                activity_id=activity.id,
                activity_title=activity.title,
                activity_date=activity.date,
                participants_count=participants_count,
                webapp_link=webapp_link,
                country=activity.country,
                city=activity.city
            )
            logger.info(f"Sent organizer checkin notification for activity {activity.id}")
        except Exception as e:
            logger.error(f"Failed to send organizer checkin notification for activity {activity.id}: {e}")


# Singleton instance
_awaiting_confirmation_service: AwaitingConfirmationService = None


def get_awaiting_confirmation_service(bot: Bot = None) -> AwaitingConfirmationService:
    """
    Get or create awaiting confirmation service instance.

    Args:
        bot: Telegram Bot instance (required on first call)

    Returns:
        AwaitingConfirmationService instance
    """
    global _awaiting_confirmation_service

    if _awaiting_confirmation_service is None:
        if bot is None:
            raise ValueError("Bot instance required for first call")
        _awaiting_confirmation_service = AwaitingConfirmationService(bot)

    return _awaiting_confirmation_service
