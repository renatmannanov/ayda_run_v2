"""
Post-Training Handler

Handles post-training flow:
1. Receiving training links from users
2. Callback buttons for "missed" and "will send later"
3. Saving links to participation records
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

from storage.db import (
    SessionLocal, User, Participation, Activity,
    PostTrainingNotification, PostTrainingNotificationStatus, ParticipationStatus
)
from bot.validators import extract_url_from_text, validate_training_link

logger = logging.getLogger(__name__)


# ============================================================================
# Database Helper Functions
# ============================================================================

def get_pending_notification(telegram_id: int):
    """
    Get pending post-training notification for user.

    Returns the most recent notification that is still waiting for response.
    """
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            return None

        notification = session.query(PostTrainingNotification).filter(
            PostTrainingNotification.user_id == user.id,
            PostTrainingNotification.status.in_([
                PostTrainingNotificationStatus.SENT,
                PostTrainingNotificationStatus.REMINDER_SENT
            ])
        ).order_by(PostTrainingNotification.sent_at.desc()).first()

        if notification:
            # Eagerly load related objects before session closes
            _ = notification.activity_id
            _ = notification.user_id
            _ = notification.status
            _ = notification.reminder_count

        return notification
    finally:
        session.close()


def save_training_link(activity_id: str, user_id: str, url: str, source: str) -> bool:
    """
    Save training link to participation record.

    Args:
        activity_id: Activity UUID
        user_id: User UUID
        url: Training link URL
        source: Link source ("manual" or "strava_auto")

    Returns:
        True if saved successfully
    """
    session = SessionLocal()
    try:
        participation = session.query(Participation).filter(
            Participation.activity_id == activity_id,
            Participation.user_id == user_id
        ).first()

        if not participation:
            logger.warning(f"Participation not found for activity={activity_id}, user={user_id}")
            return False

        participation.training_link = url
        participation.training_link_source = source
        participation.status = ParticipationStatus.ATTENDED
        participation.attended = True

        session.commit()
        logger.info(f"Saved training link for activity={activity_id}, user={user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving training link: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def update_notification_status(notification_id: str, status: PostTrainingNotificationStatus) -> bool:
    """Update notification status and set responded_at timestamp."""
    session = SessionLocal()
    try:
        notification = session.query(PostTrainingNotification).filter(
            PostTrainingNotification.id == notification_id
        ).first()

        if not notification:
            return False

        notification.status = status
        notification.responded_at = datetime.utcnow()
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating notification status: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def update_participation_to_missed(activity_id: str, user_id: str) -> bool:
    """Mark participation as missed."""
    session = SessionLocal()
    try:
        participation = session.query(Participation).filter(
            Participation.activity_id == activity_id,
            Participation.user_id == user_id
        ).first()

        if not participation:
            return False

        participation.status = ParticipationStatus.MISSED
        participation.attended = False
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating participation to missed: {e}")
        session.rollback()
        return False
    finally:
        session.close()


def get_user_and_notification_by_activity(telegram_id: int, activity_id: str):
    """Get user and their notification for a specific activity."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            return None, None

        notification = session.query(PostTrainingNotification).filter(
            PostTrainingNotification.activity_id == activity_id,
            PostTrainingNotification.user_id == user.id
        ).first()

        return user, notification
    finally:
        session.close()


def get_activity_title(activity_id: str) -> str:
    """Get activity title by ID."""
    session = SessionLocal()
    try:
        activity = session.query(Activity).filter(Activity.id == activity_id).first()
        return activity.title if activity else "Тренировка"
    finally:
        session.close()


# ============================================================================
# Message Handler for Training Links
# ============================================================================

async def handle_training_link_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle incoming message that might contain a training link.

    Only processes messages from users with pending post-training notifications.
    """
    if not update.message or not update.message.text:
        return

    # Only handle private messages
    if update.effective_chat.type != "private":
        return

    user_telegram_id = update.effective_user.id
    text = update.message.text

    # Check if user has pending notification
    notification = get_pending_notification(user_telegram_id)
    if not notification:
        # No pending notification - let other handlers process
        return

    # Try to extract URL
    url = extract_url_from_text(text)
    if not url:
        # No URL in message - might be regular text, ignore silently
        # Don't spam user with "send a link" if they're just chatting
        return

    # Validate the URL
    is_valid, error = validate_training_link(url)
    if not is_valid:
        await update.message.reply_text(f"❌ {error}")
        return

    # Save the link
    saved = save_training_link(
        activity_id=notification.activity_id,
        user_id=notification.user_id,
        url=url,
        source="manual"
    )

    if not saved:
        await update.message.reply_text("❌ Не удалось сохранить ссылку. Попробуй ещё раз.")
        return

    # Update notification status
    update_notification_status(notification.id, PostTrainingNotificationStatus.LINK_SUBMITTED)

    # Get activity title for nice message
    activity_title = get_activity_title(notification.activity_id)

    await update.message.reply_text(
        f"✅ Ссылка сохранена!\n\n"
        f"«{activity_title}»\n\n"
        f"Тренер получит её в сводке."
    )

    logger.info(f"User {user_telegram_id} submitted training link for activity {notification.activity_id}")


# ============================================================================
# Callback Handlers
# ============================================================================

async def handle_post_training_missed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle 'I was not at training' callback button.

    Callback data format: post_training_missed_{activity_id}
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("post_training_missed_"):
        return

    activity_id = data.replace("post_training_missed_", "")
    telegram_user = update.effective_user

    user, notification = get_user_and_notification_by_activity(telegram_user.id, activity_id)

    if not user:
        await query.edit_message_text("❌ Пользователь не найден")
        return

    # Update participation status
    update_participation_to_missed(activity_id, user.id)

    # Update notification status
    if notification:
        update_notification_status(notification.id, PostTrainingNotificationStatus.NOT_ATTENDED)

    activity_title = get_activity_title(activity_id)

    await query.edit_message_text(
        f"📝 Отмечено: не был(а)\n\n"
        f"«{activity_title}»\n\n"
        f"В следующий раз обязательно получится! 💪"
    )

    logger.info(f"User {telegram_user.id} marked as missed for activity {activity_id}")


async def handle_post_training_later(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle 'I was there, will send link later' callback button.

    Callback data format: post_training_later_{activity_id}
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("post_training_later_"):
        return

    activity_id = data.replace("post_training_later_", "")

    activity_title = get_activity_title(activity_id)

    # Just acknowledge - keep waiting for link
    await query.edit_message_text(
        f"👍 Хорошо!\n\n"
        f"«{activity_title}»\n\n"
        f"Отправь ссылку на тренировку, когда будет готова.\n"
        f"(Strava, Garmin, Coros, Suunto или Polar)"
    )

    logger.info(f"User {update.effective_user.id} will send link later for activity {activity_id}")


# ============================================================================
# Handler Registration
# ============================================================================

def get_post_training_handlers():
    """
    Get all post-training handlers for registration.

    Returns:
        List of handlers to be added to the bot application
    """
    return [
        # Callback handlers for buttons
        CallbackQueryHandler(handle_post_training_missed, pattern=r"^post_training_missed_"),
        CallbackQueryHandler(handle_post_training_later, pattern=r"^post_training_later_"),

        # Message handler for links - should be added with lower priority
        # than other message handlers (like feedback)
        MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
            handle_training_link_message
        ),
    ]
