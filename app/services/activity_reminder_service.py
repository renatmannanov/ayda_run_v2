"""
Activity Reminder Service

Background service that sends reminders for upcoming activities.
Runs every hour to check for activities happening in 2 days and sends reminders to:
1. Registered participants (personal chat)
2. Club/Group members (if activity is in a club/group)
3. Telegram group (if linked)
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from telegram import Bot
from sqlalchemy.orm import Session
from sqlalchemy import and_

from storage.db import (
    SessionLocal, Activity, Club, Group, Membership,
    Participation, User, ActivityStatus, ParticipationStatus
)
from app.core.timezone import utc_now
from bot.activity_notifications import (
    send_activity_reminder_to_user,
    send_activity_reminder_to_group
)
from config import settings

logger = logging.getLogger(__name__)


class ActivityReminderService:
    """
    Service to send reminders for upcoming activities (2 days before).

    Runs as a background task and checks every hour.
    """

    def __init__(self, bot: Bot, check_interval: int = 3600):
        """
        Initialize activity reminder service.

        Args:
            bot: Telegram Bot instance
            check_interval: Check interval in seconds (default: 3600 = 1 hour)
        """
        self.bot = bot
        self.check_interval = check_interval
        self._task = None
        self._running = False
        self._reminded_activities = set()  # Track already reminded activities

    async def start(self):
        """Start the reminder service"""
        if self._running:
            logger.warning("Activity reminder service is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Activity reminder service started (check interval: {self.check_interval}s)")

    async def stop(self):
        """Stop the reminder service"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Activity reminder service stopped")

    async def _run(self):
        """Main service loop"""
        while self._running:
            try:
                await self._check_and_send_reminders()
            except Exception as e:
                logger.error(f"Error in activity reminder service: {e}", exc_info=True)

            # Wait for next check
            await asyncio.sleep(self.check_interval)

    async def _check_and_send_reminders(self):
        """Check for activities in 2 days and send reminders"""
        session = SessionLocal()

        try:
            # Calculate time window for reminders
            # Use UTC time for consistent comparison with stored dates
            now = utc_now()
            target_start = now + timedelta(days=2)
            target_end = target_start + timedelta(hours=1)

            # Get upcoming activities in the time window (exclude demo activities)
            activities = session.query(Activity).filter(
                and_(
                    Activity.status == ActivityStatus.UPCOMING,
                    Activity.date >= target_start,
                    Activity.date < target_end,
                    Activity.is_demo == False
                )
            ).all()

            if not activities:
                logger.debug("No activities to remind about")
                return

            logger.info(f"Found {len(activities)} activities to send reminders for")

            # Process each activity
            for activity in activities:
                # Skip if already reminded
                if activity.id in self._reminded_activities:
                    continue

                try:
                    await self._send_reminders_for_activity(session, activity)
                    self._reminded_activities.add(activity.id)
                except Exception as e:
                    logger.error(f"Error sending reminders for activity {activity.id}: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error checking activities for reminders: {e}", exc_info=True)

        finally:
            session.close()

    async def _send_reminders_for_activity(self, session: Session, activity: Activity):
        """
        Send reminders for a single activity.

        Args:
            session: Database session
            activity: Activity to send reminders for
        """
        logger.info(f"Sending reminders for activity: {activity.title} ({activity.id})")

        # Get entity info (club or group)
        entity_name = "Активность"
        telegram_group_id = None

        if activity.club_id:
            club = session.query(Club).filter(Club.id == activity.club_id).first()
            if club:
                entity_name = club.name
                telegram_group_id = club.telegram_chat_id
        elif activity.group_id:
            group = session.query(Group).filter(Group.id == activity.group_id).first()
            if group:
                entity_name = group.name
                telegram_group_id = group.telegram_chat_id

        # Get all registered participants
        participations = session.query(Participation).filter(
            and_(
                Participation.activity_id == activity.id,
                Participation.status.in_([ParticipationStatus.REGISTERED, ParticipationStatus.CONFIRMED])
            )
        ).all()

        participants = []
        for participation in participations:
            user = session.query(User).filter(User.id == participation.user_id).first()
            if user and user.telegram_id:
                participants.append(user)

        # Send reminders to participants
        for participant in participants:
            try:
                await send_activity_reminder_to_user(
                    bot=self.bot,
                    user_telegram_id=participant.telegram_id,
                    activity_title=activity.title,
                    activity_date=activity.date,
                    location=activity.location or "Не указано",
                    is_registered=True
                )
            except Exception as e:
                logger.error(f"Failed to send reminder to participant {participant.telegram_id}: {e}")

        logger.info(f"Sent reminders to {len(participants)} participants")

        # Send reminder to Telegram group if linked
        if telegram_group_id:
            try:
                # Count participants
                participants_count = len(participants)

                await send_activity_reminder_to_group(
                    bot=self.bot,
                    group_chat_id=telegram_group_id,
                    activity_title=activity.title,
                    activity_date=activity.date,
                    participants_count=participants_count,
                    max_participants=activity.max_participants
                )
                logger.info(f"Sent reminder to Telegram group {telegram_group_id}")
            except Exception as e:
                logger.error(f"Failed to send reminder to group {telegram_group_id}: {e}")


# Singleton instance
_activity_reminder_service: Optional[ActivityReminderService] = None


def get_activity_reminder_service(bot: Bot = None) -> ActivityReminderService:
    """
    Get or create activity reminder service instance.

    Args:
        bot: Telegram Bot instance (required on first call)

    Returns:
        ActivityReminderService instance
    """
    global _activity_reminder_service

    if _activity_reminder_service is None:
        if bot is None:
            raise ValueError("Bot instance required for first call")
        _activity_reminder_service = ActivityReminderService(bot)

    return _activity_reminder_service
