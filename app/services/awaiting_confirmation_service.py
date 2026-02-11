"""
Awaiting Confirmation Service

Background service that:
1. Marks activities as COMPLETED after their end time (start + duration)
2. Transitions participations to 'awaiting' status for attendance confirmation

Runs every 5 minutes to check for:
1. Activities with status UPCOMING where end time < now
2. Participations with status 'registered' or 'confirmed' for ended activities
3. If duration is not set, defaults to 60 minutes

For each ended activity:
1. Update activity status to COMPLETED
2. Update participation statuses to AWAITING
3. Send Telegram notifications for attendance confirmation
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Callable

from telegram import Bot
from sqlalchemy.orm import Session
from sqlalchemy import and_

from storage.db import (
    SessionLocal, Participation, Activity, User,
    ParticipationStatus, ActivityStatus,
    PostTrainingNotification, PostTrainingNotificationStatus
)
from app.core.timezone import utc_now, ensure_utc_from_db
from bot.activity_notifications import (
    send_awaiting_confirmation_notification,
    send_organizer_checkin_notification,
    send_post_training_notification
)
from config import settings

logger = logging.getLogger(__name__)


class AwaitingConfirmationService:
    """
    Service to automatically:
    1. Mark ended activities as COMPLETED
    2. Transition participations to 'awaiting' status

    Runs as a background task and checks every 5 minutes.
    """

    DEFAULT_DURATION_MINUTES = 60  # Default activity duration if not specified

    def __init__(self, bot: Bot, check_interval: int = 30):  # TODO: change back to 300 after testing
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

    def _find_ended_activities(self, session: Session) -> List[Activity]:
        """
        Find all UPCOMING activities that have ended (start + duration < now).
        Includes demo activities for testing purposes.

        Args:
            session: Database session

        Returns:
            List of Activity objects that have ended
        """
        now = utc_now()

        # Get all UPCOMING activities (including demo for testing)
        upcoming_activities = session.query(Activity).filter(
            Activity.status == ActivityStatus.UPCOMING
        ).all()

        # Filter by end time in Python (for cross-database compatibility)
        ended_activities = []
        for activity in upcoming_activities:
            duration_minutes = activity.duration if activity.duration else self.DEFAULT_DURATION_MINUTES
            activity_start_utc = ensure_utc_from_db(activity.date)
            activity_end_time = activity_start_utc + timedelta(minutes=duration_minutes)

            if activity_end_time < now:
                ended_activities.append(activity)

        return ended_activities

    def _mark_activities_completed(self, session: Session, activities: List[Activity]) -> List[str]:
        """
        Mark activities as COMPLETED.

        Args:
            session: Database session
            activities: List of activities to mark as completed

        Returns:
            List of activity IDs that were marked as completed
        """
        activity_ids = []
        for activity in activities:
            activity.status = ActivityStatus.COMPLETED
            activity_ids.append(activity.id)
            logger.info(f"Marked activity {activity.id} '{activity.title}' as COMPLETED")

        return activity_ids

    def _find_participations_to_update(self, session: Session, activity_ids: List[str]) -> List[Participation]:
        """
        Find participations that need to be transitioned to AWAITING.
        Includes participations for demo activities.

        Args:
            session: Database session
            activity_ids: List of activity IDs to find participations for

        Returns:
            List of Participation objects to update
        """
        if not activity_ids:
            return []

        return session.query(Participation).filter(
            Participation.activity_id.in_(activity_ids),
            Participation.status.in_([
                ParticipationStatus.REGISTERED,
                ParticipationStatus.CONFIRMED
            ])
        ).all()

    async def _check_and_transition_participations(self):
        """
        Main method: find ended activities, mark them COMPLETED,
        and transition participations to AWAITING.

        Important: DB changes are committed BEFORE sending Telegram notifications
        to prevent spam loops (if commit fails, notifications won't be sent).
        """
        session = SessionLocal()

        try:
            # Step 1: Find ended activities
            ended_activities = self._find_ended_activities(session)

            if not ended_activities:
                logger.debug("No activities to complete")
                return

            # Step 2: Mark activities as COMPLETED
            activity_ids = self._mark_activities_completed(session, ended_activities)

            # Step 3: Find participations for these activities
            participations = self._find_participations_to_update(session, activity_ids)

            if not participations:
                session.commit()
                logger.info(f"Completed: {len(ended_activities)} activities marked COMPLETED, 0 participations")
                return

            logger.info(f"Processing {len(participations)} participations")

            # Step 4: Prepare all DB changes (status transitions + notification records)
            # Collect notification tasks to send AFTER successful commit
            pending_notifications = []
            notified_organizers = set()

            for participation in participations:
                try:
                    notification_task = await self._prepare_participation_transition(
                        session, participation, notified_organizers
                    )
                    if notification_task:
                        pending_notifications.append(notification_task)
                except Exception as e:
                    logger.error(f"Error preparing participation {participation.id}: {e}", exc_info=True)

            # Step 5: Commit all DB changes FIRST
            session.commit()

            logger.info(
                f"Committed: {len(ended_activities)} activities marked COMPLETED, "
                f"{len(participations)} participations transitioned to AWAITING"
            )

            # Step 6: Send Telegram notifications AFTER successful commit
            for task in pending_notifications:
                try:
                    await task()
                except Exception as e:
                    logger.error(f"Error sending notification: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Error in check_and_transition_participations: {e}", exc_info=True)
            session.rollback()

        finally:
            session.close()

    async def _prepare_participation_transition(
        self,
        session: Session,
        participation: Participation,
        notified_organizers: set
    ):
        """
        Prepare DB changes for a single participation transition.
        Returns a coroutine callable that sends Telegram notifications,
        or None if no notification is needed.

        DB changes (status update, notification records) are added to session
        but NOT committed — the caller commits after all participations are prepared.
        Telegram messages are sent only after successful commit.

        Args:
            session: Database session
            participation: Participation to transition
            notified_organizers: Set of activity IDs for which organizer was already notified

        Returns:
            Async callable to send notification, or None
        """
        # Update participation status (always, including demo)
        participation.status = ParticipationStatus.AWAITING

        # Get user and activity for notification
        user = session.query(User).filter(User.id == participation.user_id).first()
        activity = session.query(Activity).filter(Activity.id == participation.activity_id).first()

        if not activity:
            logger.warning(f"Activity {participation.activity_id} not found")
            return None

        # Skip notifications for demo activities (status already updated above)
        if activity.is_demo:
            logger.debug(f"Skipping notification for demo activity {activity.id}")
            return None

        # Check if this is a club/group activity
        is_club_group_activity = activity.club_id or activity.group_id

        if not user or not user.telegram_id:
            logger.warning(f"User {participation.user_id} not found or has no telegram_id")
            return None

        if is_club_group_activity:
            is_organizer = user.id == activity.creator_id

            # Capture values for the deferred notification closure
            user_id = user.id
            user_telegram_id = user.telegram_id
            user_strava = user.strava_athlete_id
            activity_id = activity.id
            activity_title = activity.title
            activity_date = activity.date
            activity_location = activity.location or "Не указано"
            activity_country = activity.country
            activity_city = activity.city
            activity_key = str(activity.id)

            if not is_organizer and not user_strava:
                # Create PostTrainingNotification record in DB (before commit)
                notification = PostTrainingNotification(
                    activity_id=activity_id,
                    user_id=user_id,
                    status=PostTrainingNotificationStatus.SENT
                )
                session.add(notification)

            if user_strava and not is_organizer:
                logger.info(
                    f"Skipping post-training notification for user {user_id} "
                    f"(Strava connected, waiting for webhook)"
                )

            # Track organizer notification
            should_notify_organizer = activity_key not in notified_organizers
            if should_notify_organizer:
                notified_organizers.add(activity_key)

            # Return deferred notification sender
            async def send_notifications():
                if not is_organizer and not user_strava:
                    try:
                        await send_post_training_notification(
                            bot=self.bot,
                            user_telegram_id=user_telegram_id,
                            activity_id=activity_id,
                            activity_title=activity_title,
                            activity_date=activity_date,
                            location=activity_location,
                            country=activity_country,
                            city=activity_city
                        )
                        logger.info(f"Sent post-training notification to user {user_id} for activity {activity_id}")
                    except Exception as e:
                        logger.error(f"Failed to send post-training notification to user {user_id}: {e}")

                if should_notify_organizer:
                    # Re-open session for organizer lookup (original session may be closed)
                    organizer_session = SessionLocal()
                    try:
                        organizer_activity = organizer_session.query(Activity).filter(
                            Activity.id == activity_id
                        ).first()
                        if organizer_activity:
                            await self._notify_organizer(organizer_session, organizer_activity)
                    finally:
                        organizer_session.close()

            return send_notifications

        else:
            # Personal activity — capture values for deferred notification
            user_id = user.id
            user_telegram_id = user.telegram_id
            activity_id = activity.id
            activity_title = activity.title
            activity_date = activity.date
            activity_location = activity.location or "Не указано"
            activity_country = activity.country
            activity_city = activity.city

            async def send_personal_notification():
                try:
                    await send_awaiting_confirmation_notification(
                        bot=self.bot,
                        user_telegram_id=user_telegram_id,
                        activity_id=activity_id,
                        activity_title=activity_title,
                        activity_date=activity_date,
                        location=activity_location,
                        country=activity_country,
                        city=activity_city
                    )
                    logger.info(f"Sent awaiting confirmation notification to user {user_id} for activity {activity_id}")
                except Exception as e:
                    logger.error(f"Failed to send awaiting confirmation notification to user {user_id}: {e}")

            return send_personal_notification

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

        # TODO: Re-enable when attendance marking is needed again
        # Currently disabled because post-training flow collects links instead
        # # Count participants
        # participants_count = session.query(Participation).filter(
        #     Participation.activity_id == activity.id
        # ).count()
        #
        # # Build webapp link
        # webapp_link = f"{settings.app_url}activity/{activity.id}"
        #
        # try:
        #     await send_organizer_checkin_notification(
        #         bot=self.bot,
        #         organizer_telegram_id=organizer.telegram_id,
        #         activity_id=activity.id,
        #         activity_title=activity.title,
        #         activity_date=activity.date,
        #         participants_count=participants_count,
        #         webapp_link=webapp_link,
        #         country=activity.country,
        #         city=activity.city
        #     )
        #     logger.info(f"Sent organizer checkin notification for activity {activity.id}")
        # except Exception as e:
        #     logger.error(f"Failed to send organizer checkin notification for activity {activity.id}: {e}")
        logger.info(f"Skipping organizer checkin notification for activity {activity.id} (disabled)")


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
