"""
Feedback Handler

Handles text messages from users in private chat.
Saves feedback to database and forwards to feedback group.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

from storage.db import SessionLocal, User
from storage.feedback_storage import save_feedback
from config import settings

logger = logging.getLogger(__name__)


async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle text messages in private chat as feedback.

    Saves the message to database and forwards it to the feedback group.
    """
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    message = update.message
    text = message.text

    # Skip if message is too short (likely accidental)
    if len(text.strip()) < 3:
        return

    logger.info(f"Received feedback from user {user.id}: {text[:100]}...")

    db = SessionLocal()
    try:
        # Find user in database if exists
        db_user = db.query(User).filter(User.telegram_id == user.id).first()
        user_id = db_user.id if db_user else None

        # Save feedback to database
        feedback = save_feedback(
            db=db,
            telegram_id=user.id,
            message=text,
            message_id=message.message_id,
            user_id=user_id
        )
        logger.info(f"Feedback saved with ID: {feedback.id}")

        # Forward to feedback group if configured
        feedback_chat_id = getattr(settings, 'feedback_chat_id', None)
        if feedback_chat_id:
            # Format user info
            user_link = f"@{user.username}" if user.username else f"tg://user?id={user.id}"
            user_name = user.full_name or user.first_name or "Unknown"

            # Format message for group
            forward_text = (
                f"📬 <b>Новый фидбек</b>\n\n"
                f"👤 <b>От:</b> {user_name} ({user_link})\n"
                f"🆔 <b>ID:</b> <code>{user.id}</code>\n\n"
                f"💬 <b>Сообщение:</b>\n{text}"
            )

            try:
                await context.bot.send_message(
                    chat_id=feedback_chat_id,
                    text=forward_text,
                    parse_mode=ParseMode.HTML
                )
                logger.info(f"Feedback forwarded to group {feedback_chat_id}")
            except Exception as e:
                logger.error(f"Failed to forward feedback to group: {e}")

        # Reply to user
        await message.reply_text(
            "Спасибо за обратную связь! Ваше сообщение сохранено. 🙏"
        )

    except Exception as e:
        logger.error(f"Error handling feedback: {e}", exc_info=True)
        await message.reply_text(
            "Произошла ошибка при сохранении сообщения. Попробуйте позже."
        )
    finally:
        db.close()


def get_feedback_handler() -> MessageHandler:
    """
    Get the feedback message handler.

    Returns a MessageHandler that catches text messages in private chats
    that are not commands.
    """
    return MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_feedback
    )
