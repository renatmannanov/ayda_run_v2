"""
Admin Notifications for Telegram Bot

Handles sending notifications to admin about club requests and other events.
"""

import logging
from typing import Dict, Any, Optional
from telegram import Bot
from telegram.error import TelegramError

from config import settings
from bot.keyboards import get_admin_approval_keyboard
from bot.messages import format_admin_club_request_notification
from storage.club_storage import ClubStorage
from storage.user_storage import UserStorage

logger = logging.getLogger(__name__)


async def send_club_request_notification(
    bot: Bot,
    request_id: str,
    request_data: Dict[str, Any]
) -> bool:
    """
    Send notification to admin about new club request.

    Args:
        bot: Telegram Bot instance
        request_id: ClubRequest UUID
        request_data: Dictionary with club request data

    Returns:
        True if notification was sent successfully, False otherwise
    """
    try:
        # Get admin chat ID from settings
        admin_chat_id = settings.admin_chat_id

        if not admin_chat_id:
            logger.warning("ADMIN_CHAT_ID not set in settings, skipping admin notification")
            return False

        # Get user info for notification
        user_id = request_data.get('user_id')
        if user_id:
            with UserStorage() as user_storage:
                user = user_storage.get_user_by_id(user_id)
                if user:
                    request_data['user_name'] = f"{user.first_name} {user.last_name or ''}".strip()
                    request_data['username'] = user.username

        # Format notification message
        message = format_admin_club_request_notification(request_data)

        # Send notification with approval keyboard
        await bot.send_message(
            chat_id=admin_chat_id,
            text=message,
            reply_markup=get_admin_approval_keyboard(request_id)
        )

        logger.info(f"Admin notification sent for club request {request_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending admin notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in send_club_request_notification: {e}")
        return False


async def handle_admin_approval(bot: Bot, callback_query) -> None:
    """
    Handle admin approval/rejection of club request.

    Args:
        bot: Telegram Bot instance
        callback_query: CallbackQuery from admin's button click
    """
    try:
        await callback_query.answer()

        data = callback_query.data  # approve_club_{request_id} or reject_club_{request_id}

        if data.startswith("approve_club_"):
            request_id = data.replace("approve_club_", "")
            await handle_club_approval(bot, callback_query, request_id)

        elif data.startswith("reject_club_"):
            request_id = data.replace("reject_club_", "")
            await handle_club_rejection(bot, callback_query, request_id)

    except Exception as e:
        logger.error(f"Error in handle_admin_approval: {e}")
        await callback_query.answer("❌ Ошибка при обработке", show_alert=True)


async def handle_club_approval(bot: Bot, callback_query, request_id: str) -> None:
    """
    Handle club request approval.

    Args:
        bot: Telegram Bot instance
        callback_query: CallbackQuery from admin
        request_id: ClubRequest UUID
    """
    try:
        with ClubStorage() as club_storage:
            request = club_storage.get_club_request_by_id(request_id)

            if not request:
                await callback_query.answer("❌ Заявка не найдена", show_alert=True)
                return

            # Update request status
            from storage.db import ClubRequestStatus
            club_storage.update_club_request_status(request_id, ClubRequestStatus.APPROVED)

            # Update message
            await callback_query.edit_message_text(
                text=f"{callback_query.message.text}\n\n✅ ОДОБРЕНО",
                reply_markup=None
            )

            # Notify user about approval
            with UserStorage() as user_storage:
                user = user_storage.get_user_by_id(request.user_id)
                if user:
                    try:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=f"🎉 Отличные новости!\n\n"
                                 f"Твоя заявка на создание клуба '{request.name}' одобрена!\n\n"
                                 f"Скоро мы свяжемся с тобой для финальной настройки."
                        )
                    except TelegramError as e:
                        logger.error(f"Error notifying user about approval: {e}")

            await callback_query.answer("✅ Заявка одобрена", show_alert=True)
            logger.info(f"Club request {request_id} approved by admin")

    except Exception as e:
        logger.error(f"Error in handle_club_approval: {e}")
        await callback_query.answer("❌ Ошибка при одобрении", show_alert=True)


async def handle_club_rejection(bot: Bot, callback_query, request_id: str) -> None:
    """
    Handle club request rejection.

    Args:
        bot: Telegram Bot instance
        callback_query: CallbackQuery from admin
        request_id: ClubRequest UUID
    """
    try:
        with ClubStorage() as club_storage:
            request = club_storage.get_club_request_by_id(request_id)

            if not request:
                await callback_query.answer("❌ Заявка не найдена", show_alert=True)
                return

            # Update request status
            from storage.db import ClubRequestStatus
            club_storage.update_club_request_status(request_id, ClubRequestStatus.REJECTED)

            # Update message
            await callback_query.edit_message_text(
                text=f"{callback_query.message.text}\n\n❌ ОТКЛОНЕНО",
                reply_markup=None
            )

            # Notify user about rejection
            with UserStorage() as user_storage:
                user = user_storage.get_user_by_id(request.user_id)
                if user:
                    try:
                        await bot.send_message(
                            chat_id=user.telegram_id,
                            text=f"К сожалению, заявка на создание клуба '{request.name}' не была одобрена.\n\n"
                                 f"Если у тебя есть вопросы, свяжись с нами: @aydarun_support"
                        )
                    except TelegramError as e:
                        logger.error(f"Error notifying user about rejection: {e}")

            await callback_query.answer("❌ Заявка отклонена", show_alert=True)
            logger.info(f"Club request {request_id} rejected by admin")

    except Exception as e:
        logger.error(f"Error in handle_club_rejection: {e}")
        await callback_query.answer("❌ Ошибка при отклонении", show_alert=True)
