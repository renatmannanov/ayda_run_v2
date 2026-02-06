"""
Post-Training Summary Service

Background service that:
1. Sends reminders to participants who haven't submitted links (3h after notification)
2. Sends summary to trainers/organizers (5h after activity end)

Uses PostTrainingNotification table to track notification states.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from sqlalchemy.orm import Session

from storage.db import (
    SessionLocal, Participation, Activity, User,
    PostTrainingNotification, PostTrainingNotificationStatus,
    ParticipationStatus, ActivityStatus
)
from app.core.timezone import utc_now, format_datetime_local
from app_config.constants import (
    POST_TRAINING_REMINDER_DELAY_HOURS,
    POST_TRAINING_SUMMARY_DELAY_HOURS,
    POST_TRAINING_MAX_REMINDERS
)

logger = logging.getLogger(__name__)


class PostTrainingSummaryService:
    """
    Service to send:
    1. Reminders to participants (3h after initial notification)
    2. Summary to trainers (5h after activity end)

    Runs as a background task.
    """

    def __init__(self, bot: Bot, check_interval: int = 300):
        """
        Initialize post-training summary service.

        Args:
            bot: Telegram Bot instance
            check_interval: Check interval in seconds (default: 300 = 5 minutes)
        """
        self.bot = bot
        self.check_interval = check_interval
        self._task = None
        self._running = False
        self._sent_summaries = set()  # Track activities for which summary was sent

    async def start(self):
        """Start the service"""
        if self._running:
            logger.warning("Post-training summary service is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info(f"Post-training summary service started (check interval: {self.check_interval}s)")

    async def stop(self):
        """Stop the service"""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Post-training summary service stopped")

    async def _run(self):
        """Main service loop"""
        while self._running:
            try:
                await self._process_pending_reminders()
                await self._process_trainer_summaries()
            except Exception as e:
                logger.error(f"Error in post-training summary service: {e}", exc_info=True)

            await asyncio.sleep(self.check_interval)

    # =========================================================================
    # Participant Reminders (3h after notification)
    # =========================================================================

    async def _process_pending_reminders(self):
        """Send reminders to participants who haven't responded after 3 hours."""
        session = SessionLocal()
        try:
            cutoff = utc_now() - timedelta(hours=POST_TRAINING_REMINDER_DELAY_HOURS)

            # Find notifications that were sent but not responded to
            notifications = session.query(PostTrainingNotification).filter(
                PostTrainingNotification.status == PostTrainingNotificationStatus.SENT,
                PostTrainingNotification.sent_at < cutoff,
                PostTrainingNotification.reminder_count < POST_TRAINING_MAX_REMINDERS
            ).all()

            if not notifications:
                return

            logger.info(f"Processing {len(notifications)} pending reminders")

            for notification in notifications:
                try:
                    await self._send_participant_reminder(session, notification)
                except Exception as e:
                    logger.error(f"Error sending reminder for notification {notification.id}: {e}")

            session.commit()

        except Exception as e:
            logger.error(f"Error processing pending reminders: {e}", exc_info=True)
            session.rollback()
        finally:
            session.close()

    async def _send_participant_reminder(
        self,
        session: Session,
        notification: PostTrainingNotification
    ):
        """Send reminder to a single participant."""
        user = session.query(User).filter(User.id == notification.user_id).first()
        activity = session.query(Activity).filter(
            Activity.id == notification.activity_id
        ).first()

        if not user or not user.telegram_id or not activity:
            logger.warning(f"Missing data for notification {notification.id}")
            return

        # Build keyboard with "missed" button
        keyboard = [[
            InlineKeyboardButton(
                "Не был(а)",
                callback_data=f"post_training_missed_{activity.id}"
            )
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"⏰ Напоминание: отправь ссылку на тренировку\n\n"
            f"«{activity.title}»\n\n"
            f"Strava, Garmin, Coros, Suunto или Polar."
        )

        try:
            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=message,
                reply_markup=reply_markup
            )

            # Update notification
            notification.status = PostTrainingNotificationStatus.REMINDER_SENT
            notification.reminder_count += 1

            logger.info(f"Sent reminder to user {user.id} for activity {activity.id}")

        except TelegramError as e:
            logger.error(f"Failed to send reminder to user {user.telegram_id}: {e}")

    # =========================================================================
    # Trainer Summary (5h after activity end)
    # =========================================================================

    async def _process_trainer_summaries(self):
        """Send summaries to trainers 5 hours after activity end."""
        session = SessionLocal()
        try:
            now = utc_now()

            # Find completed club/group activities
            activities = session.query(Activity).filter(
                Activity.status == ActivityStatus.COMPLETED,
                Activity.is_demo == False
            ).filter(
                (Activity.club_id != None) | (Activity.group_id != None)
            ).all()

            for activity in activities:
                # Skip if already sent summary
                if str(activity.id) in self._sent_summaries:
                    continue

                # Check if 5 hours have passed since activity end
                duration_minutes = activity.duration or 60
                activity_end = activity.date + timedelta(minutes=duration_minutes)
                summary_time = activity_end + timedelta(hours=POST_TRAINING_SUMMARY_DELAY_HOURS)

                if now < summary_time:
                    continue

                try:
                    await self._send_trainer_summary(session, activity)
                    self._sent_summaries.add(str(activity.id))
                except Exception as e:
                    logger.error(f"Error sending summary for activity {activity.id}: {e}")

        except Exception as e:
            logger.error(f"Error processing trainer summaries: {e}", exc_info=True)
        finally:
            session.close()

    async def _send_trainer_summary(self, session: Session, activity: Activity):
        """Send summary to trainer for a single activity."""
        # Get trainer (creator)
        trainer = session.query(User).filter(User.id == activity.creator_id).first()
        if not trainer or not trainer.telegram_id:
            logger.warning(f"Trainer not found for activity {activity.id}")
            return

        # Get all participations (excluding trainer)
        participations = session.query(Participation).filter(
            Participation.activity_id == activity.id,
            Participation.user_id != activity.creator_id
        ).all()

        if not participations:
            logger.info(f"No participants for activity {activity.id}, skipping summary")
            return

        # Categorize participants
        submitted = []
        pending = []
        missed = []

        for p in participations:
            user = session.query(User).filter(User.id == p.user_id).first()
            if not user:
                continue

            name = user.first_name or user.username or "Участник"

            if p.training_link:
                submitted.append((name, p.training_link))
            elif p.status == ParticipationStatus.MISSED:
                missed.append(name)
            else:
                pending.append(name)

        # Format summary message
        total = len(participations)
        date_str = format_datetime_local(
            activity.date,
            activity.country,
            activity.city,
            "%d %B"
        )

        lines = [
            f"📋 Сводка: {activity.title}",
            f"{date_str}",
            ""
        ]

        if submitted:
            lines.append(f"Прикрепили ({len(submitted)}/{total}):")
            for name, link in submitted:
                lines.append(f"✅ {name} 🔗")
            lines.append("")

        if pending:
            lines.append(f"Не ответили ({len(pending)}/{total}):")
            for name in pending:
                lines.append(f"⏳ {name}")
            lines.append("")

        if missed:
            lines.append("Не были:")
            for name in missed:
                lines.append(f"❌ {name}")
            lines.append("")

        message = "\n".join(lines)

        # Build keyboard
        buttons = []
        if pending:
            buttons.append([
                InlineKeyboardButton(
                    "📩 Напомнить неответившим",
                    callback_data=f"remind_pending_{activity.id}"
                )
            ])

        reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

        try:
            await self.bot.send_message(
                chat_id=trainer.telegram_id,
                text=message,
                reply_markup=reply_markup
            )
            logger.info(f"Sent trainer summary for activity {activity.id}")

        except TelegramError as e:
            logger.error(f"Failed to send trainer summary to {trainer.telegram_id}: {e}")


# ============================================================================
# Singleton Instance
# ============================================================================

_post_training_summary_service: Optional[PostTrainingSummaryService] = None


def get_post_training_summary_service(bot: Bot = None) -> PostTrainingSummaryService:
    """
    Get or create post-training summary service instance.

    Args:
        bot: Telegram Bot instance (required on first call)

    Returns:
        PostTrainingSummaryService instance
    """
    global _post_training_summary_service

    if _post_training_summary_service is None:
        if bot is None:
            raise ValueError("Bot instance required for first call")
        _post_training_summary_service = PostTrainingSummaryService(bot)

    return _post_training_summary_service
