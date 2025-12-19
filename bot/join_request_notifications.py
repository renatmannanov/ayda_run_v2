"""
Join Request Notifications

Handles sending notifications for join request events:
- New join request to organizer
- Approval notification to user
- Rejection notification to user
- Expiry notification to user
"""

import logging
from typing import Optional, Dict, Any
from telegram import Bot
from telegram.error import TelegramError

from bot.messages import (
    format_join_request_notification,
    format_approval_notification,
    format_rejection_notification,
    format_expired_request_notification
)
from bot.keyboards import get_join_request_keyboard

logger = logging.getLogger(__name__)


async def send_join_request_to_organizer(
    bot: Bot,
    organizer_telegram_id: int,
    user_data: Dict[str, Any],
    entity_data: Dict[str, Any],
    request_id: str
) -> bool:
    """
    Send join request notification to organizer with approve/reject buttons.

    Args:
        bot: Telegram Bot instance
        organizer_telegram_id: Organizer's Telegram ID
        user_data: Dictionary with user info (first_name, username, preferred_sports, strava_link)
        entity_data: Dictionary with entity info (name, type, id)
        request_id: JoinRequest UUID

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        entity_type = entity_data.get('type', 'club')

        # Format message
        message_text = format_join_request_notification(user_data, entity_data)

        # Get keyboard
        keyboard = get_join_request_keyboard(request_id, entity_type)

        # Send message
        await bot.send_message(
            chat_id=organizer_telegram_id,
            text=message_text,
            reply_markup=keyboard
        )

        logger.info(f"Sent join request notification to organizer {organizer_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending join request notification: {e}")
        return False


async def send_approval_notification(
    bot: Bot,
    user_telegram_id: int,
    entity_name: str,
    entity_type: str
) -> bool:
    """
    Send approval notification to user.

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        entity_name: Name of club/group/activity
        entity_type: "club", "group", or "activity"

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_approval_notification(entity_name, entity_type)

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text
        )

        logger.info(f"Sent approval notification to user {user_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending approval notification: {e}")
        return False


async def send_rejection_notification(
    bot: Bot,
    user_telegram_id: int,
    entity_name: str,
    entity_type: str
) -> bool:
    """
    Send rejection notification to user.

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        entity_name: Name of club/group/activity
        entity_type: "club", "group", or "activity"

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_rejection_notification(entity_name, entity_type)

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text
        )

        logger.info(f"Sent rejection notification to user {user_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending rejection notification: {e}")
        return False


async def send_expiry_notification(
    bot: Bot,
    user_telegram_id: int,
    entity_name: str,
    entity_type: str = "activity"
) -> bool:
    """
    Send expiry notification to user (for activities).

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        entity_name: Name of activity
        entity_type: "activity" (default)

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_expired_request_notification(entity_name, entity_type)

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text
        )

        logger.info(f"Sent expiry notification to user {user_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending expiry notification: {e}")
        return False
