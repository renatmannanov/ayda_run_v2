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
from typing import Optional

from urllib.parse import urlparse

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from sqlalchemy.orm import Session
from storage.db import (
    SessionLocal, Participation, Activity, User,
    PostTrainingNotification, PostTrainingNotificationStatus,
    ParticipationStatus, ActivityStatus
)
from app.core.timezone import utc_now, format_datetime_local, ensure_utc_from_db
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
        """Send reminders to participants who haven't responded after 3 hours.

        Pattern: update DB status first, commit, then send Telegram messages.
        """
        session = SessionLocal()
        try:
            # sent_at is stored as naive UTC, so cutoff must also be naive
            cutoff = datetime.utcnow() - timedelta(hours=POST_TRAINING_REMINDER_DELAY_HOURS)

            # Find notifications that were sent but not responded to
            notifications = session.query(PostTrainingNotification).filter(
                PostTrainingNotification.status == PostTrainingNotificationStatus.SENT,
                PostTrainingNotification.sent_at < cutoff,
                PostTrainingNotification.reminder_count < POST_TRAINING_MAX_REMINDERS
            ).all()

            if not notifications:
                return

            logger.info(f"Processing {len(notifications)} pending reminders")

            # Step 1: Prepare DB changes and collect notification tasks
            pending_sends = []
            for notification in notifications:
                try:
                    send_task = self._prepare_participant_reminder(session, notification)
                    if send_task:
                        pending_sends.append(send_task)
                except Exception as e:
                    logger.error(f"Error preparing reminder for notification {notification.id}: {e}")

            # Step 2: Commit DB changes FIRST
            session.commit()

            # Step 3: Send Telegram messages AFTER successful commit
            for send_task in pending_sends:
                try:
                    await send_task()
                except Exception as e:
                    logger.error(f"Error sending reminder: {e}")

        except Exception as e:
            logger.error(f"Error processing pending reminders: {e}", exc_info=True)
            session.rollback()
        finally:
            session.close()

    def _prepare_participant_reminder(
        self,
        session: Session,
        notification: PostTrainingNotification
    ):
        """Prepare DB changes for reminder and return a send task.

        Returns an async callable to send the Telegram message, or None.
        DB status is updated before commit; message sent after commit.
        """
        user = session.query(User).filter(User.id == notification.user_id).first()
        activity = session.query(Activity).filter(
            Activity.id == notification.activity_id
        ).first()

        if not user or not user.telegram_id or not activity:
            logger.warning(f"Missing data for notification {notification.id}")
            return None

        # Skip reminder if link was already submitted (e.g. via Strava auto-link)
        participation = session.query(Participation).filter(
            Participation.activity_id == notification.activity_id,
            Participation.user_id == notification.user_id
        ).first()
        if participation and participation.training_link:
            notification.status = PostTrainingNotificationStatus.LINK_SUBMITTED
            notification.responded_at = datetime.utcnow()
            logger.info(
                f"Skipping reminder for user {user.id} — link already submitted "
                f"(source: {participation.training_link_source})"
            )
            return None

        # Update DB status BEFORE commit (will be committed by caller)
        notification.status = PostTrainingNotificationStatus.REMINDER_SENT
        notification.reminder_count += 1

        # Capture values for deferred send
        user_id = user.id
        user_telegram_id = user.telegram_id
        activity_id = activity.id
        activity_title = activity.title

        async def send():
            keyboard = [[
                InlineKeyboardButton(
                    "Не был(а)",
                    callback_data=f"post_training_missed_{activity_id}"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            message = (
                f"⏰ Напоминание: отправь ссылку на тренировку «{activity_title}»\n\n"
                f"Тогда тренер сможет её проанализировать и предоставить тебе обратную связь."
                # TODO: uncomment when Strava API quota is approved
                # f"\n\nА чтобы всё было автоматически, подключи Strava /connect_strava"
            )

            try:
                await self.bot.send_message(
                    chat_id=user_telegram_id,
                    text=message,
                    reply_markup=reply_markup
                )
                logger.info(f"Sent reminder to user {user_id} for activity {activity_id}")
            except TelegramError as e:
                logger.error(f"Failed to send reminder to user {user_telegram_id}: {e}")

        return send

    # =========================================================================
    # Trainer Summary (5h after activity end)
    # =========================================================================

    async def _process_trainer_summaries(self):
        """Send summaries to trainers 5 hours after activity end.

        Uses activity.summary_sent_at DB field to track sent summaries
        (survives restarts, unlike in-memory cache).
        Pattern: mark as sent in DB, commit, then send message.
        """
        session = SessionLocal()
        try:
            now = utc_now()

            # Find completed club/group activities where summary hasn't been sent yet
            activities = session.query(Activity).filter(
                Activity.status == ActivityStatus.COMPLETED,
                Activity.is_demo == False,
                Activity.summary_sent_at == None
            ).filter(
                (Activity.club_id != None) | (Activity.group_id != None)
            ).all()

            # Step 1: Collect activities ready for summary and prepare send tasks
            pending_sends = []
            for activity in activities:
                # Check if enough time has passed since activity end
                duration_minutes = activity.duration or 60
                activity_date_utc = ensure_utc_from_db(activity.date)
                activity_end = activity_date_utc + timedelta(minutes=duration_minutes)
                summary_time = activity_end + timedelta(hours=POST_TRAINING_SUMMARY_DELAY_HOURS)

                if now < summary_time:
                    continue

                send_task = self._prepare_trainer_summary(session, activity)
                # Mark as sent regardless (prevents re-checking activities with no participants)
                activity.summary_sent_at = datetime.utcnow()
                if send_task:
                    pending_sends.append(send_task)

            if not pending_sends:
                # Still commit to persist summary_sent_at for skipped activities
                session.commit()
                return

            # Step 2: Commit DB changes FIRST
            session.commit()

            # Step 3: Send Telegram messages AFTER successful commit
            for send_task in pending_sends:
                try:
                    await send_task()
                except Exception as e:
                    logger.error(f"Error sending trainer summary: {e}")

        except Exception as e:
            logger.error(f"Error processing trainer summaries: {e}", exc_info=True)
            session.rollback()
        finally:
            session.close()

    def _prepare_trainer_summary(self, session: Session, activity: Activity):
        """Prepare trainer summary data and return an async send task.

        Returns an async callable to send the Telegram message, or None.
        Does NOT modify DB — caller handles marking summary_sent_at.
        """
        # Get trainer (creator)
        trainer = session.query(User).filter(User.id == activity.creator_id).first()
        if not trainer or not trainer.telegram_id:
            logger.warning(f"Trainer not found for activity {activity.id}")
            return None

        # Get all participations (excluding trainer)
        participations = session.query(Participation).filter(
            Participation.activity_id == activity.id,
            Participation.user_id != activity.creator_id
        ).all()

        if not participations:
            logger.info(f"No participants for activity {activity.id}, skipping summary")
            return None

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

        location = activity.location or ""
        location_part = f" · {location}" if location else ""

        lines = [
            f"📋 Собранные данные по тренировке «{activity.title}»",
            f"{date_str}{location_part}",
            ""
        ]

        if submitted:
            lines.append(f"Прикрепили ({len(submitted)}/{total}):")
            for name, link in submitted:
                try:
                    parsed = urlparse(link)
                    short_link = parsed.netloc + parsed.path
                except Exception:
                    short_link = link
                lines.append(f"▪️ {name} {short_link}")
            lines.append("")

        if pending:
            lines.append(f"Не ответили ({len(pending)}/{total}):")
            lines.append(f"⏳ {', '.join(pending)}")
            lines.append("")

        if missed:
            lines.append("Не были:")
            lines.append(f"❌ {', '.join(missed)}")
            lines.append("")

        message = "\n".join(lines)

        # Capture values for deferred send
        trainer_telegram_id = trainer.telegram_id
        activity_id = activity.id
        has_pending = bool(pending)

        async def send():
            buttons = []
            if has_pending:
                buttons.append([
                    InlineKeyboardButton(
                        "📩 Напомнить",
                        callback_data=f"remind_pending_{activity_id}"
                    )
                ])

            reply_markup = InlineKeyboardMarkup(buttons) if buttons else None

            try:
                await self.bot.send_message(
                    chat_id=trainer_telegram_id,
                    text=message,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                logger.info(f"Sent trainer summary for activity {activity_id}")
            except TelegramError as e:
                logger.error(f"Failed to send trainer summary to {trainer_telegram_id}: {e}")

        return send


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
