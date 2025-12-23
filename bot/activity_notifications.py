"""
Activity Notifications

Handles sending notifications for activity events:
- New activity created (to club/group members)
- Activity reminder (2 days before)
- Notifications to both personal chats and Telegram groups (if linked)
"""

import logging
from typing import Optional, List
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


def format_new_activity_notification(
    activity_title: str,
    activity_date: datetime,
    location: str,
    participants_count: int,
    max_participants: Optional[int],
    entity_name: str,
    webapp_link: str
) -> str:
    """
    Format notification message for new activity.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location
        participants_count: Current number of participants
        max_participants: Maximum participants (None if unlimited)
        entity_name: Club/Group name
        webapp_link: Link to activity in webapp

    Returns:
        Formatted message text
    """
    # Format date
    date_str = activity_date.strftime("%d %B в %H:%M")

    # Format participants
    if max_participants:
        participants_str = f"{participants_count}/{max_participants} участников"
    else:
        participants_str = f"{participants_count} участников"

    message = (
        f"🏃 Новая активность в \"{entity_name}\"!\n\n"
        f"⛰️ {activity_title}\n"
        f"📅 {date_str}\n"
        f"📍 {location}\n"
        f"👥 {participants_str}\n\n"
        f"[Открыть в приложении 🔗]({webapp_link})"
    )

    return message


def format_new_activity_group_notification(
    activity_title: str,
    activity_date: datetime,
    location: str,
    webapp_link: str
) -> str:
    """
    Format notification message for Telegram group posting.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location
        webapp_link: Link to activity in webapp

    Returns:
        Formatted message text for group
    """
    # Format date
    date_str = activity_date.strftime("%d %B в %H:%M")

    message = (
        f"@channel Новая активность!\n\n"
        f"⛰️ {activity_title}\n"
        f"📅 {date_str}\n"
        f"📍 {location}\n\n"
        f"Записаться: {webapp_link}"
    )

    return message


def format_activity_reminder_notification(
    activity_title: str,
    activity_date: datetime,
    location: str,
    is_registered: bool = True
) -> str:
    """
    Format reminder notification (2 days before activity).

    Args:
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location
        is_registered: Whether user is registered for activity

    Returns:
        Formatted message text
    """
    # Format date
    date_str = activity_date.strftime("%d %B в %H:%M")

    message = (
        f"⏰ Напоминание!\n\n"
        f"Через 2 дня:\n"
        f"🏃 {activity_title}\n"
        f"📅 {date_str}\n"
        f"📍 {location}\n"
    )

    if is_registered:
        message += "\nВы записаны! ✅"

    return message


def format_activity_reminder_group_notification(
    activity_title: str,
    activity_date: datetime,
    participants_count: int,
    max_participants: Optional[int]
) -> str:
    """
    Format reminder notification for Telegram group.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time
        participants_count: Current number of participants
        max_participants: Maximum participants (None if unlimited)

    Returns:
        Formatted message text for group
    """
    # Format date
    date_str = activity_date.strftime("%d %B в %H:%M")

    # Format participants
    if max_participants:
        participants_str = f"{participants_count}/{max_participants} участников"
    else:
        participants_str = f"{participants_count} участников"

    message = (
        f"⏰ Через 2 дня активность!\n\n"
        f"🏃 {activity_title}\n"
        f"📅 {date_str}\n\n"
        f"Записано: {participants_str}"
    )

    return message


async def send_new_activity_notification_to_user(
    bot: Bot,
    user_telegram_id: int,
    activity_title: str,
    activity_date: datetime,
    location: str,
    participants_count: int,
    max_participants: Optional[int],
    entity_name: str,
    webapp_link: str
) -> bool:
    """
    Send new activity notification to a single user.

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location
        participants_count: Current number of participants
        max_participants: Maximum participants
        entity_name: Club/Group name
        webapp_link: Link to activity in webapp

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_new_activity_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            location=location,
            participants_count=participants_count,
            max_participants=max_participants,
            entity_name=entity_name,
            webapp_link=webapp_link
        )

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )

        logger.info(f"Sent new activity notification to user {user_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending new activity notification to user {user_telegram_id}: {e}")
        return False


async def send_new_activity_notification_to_group(
    bot: Bot,
    group_chat_id: int,
    activity_title: str,
    activity_date: datetime,
    location: str,
    webapp_link: str
) -> bool:
    """
    Send new activity notification to Telegram group.

    Args:
        bot: Telegram Bot instance
        group_chat_id: Telegram group chat ID
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location
        webapp_link: Link to activity in webapp

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        message_text = format_new_activity_group_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            location=location,
            webapp_link=webapp_link
        )

        # Remove the link from text since we'll use a button
        message_text = message_text.replace(f"\n\nЗаписаться: {webapp_link}", "")

        # Create inline button for the link
        keyboard = [[
            InlineKeyboardButton("Записаться 🔗", url=webapp_link)
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(
            chat_id=group_chat_id,
            text=message_text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

        logger.info(f"Sent new activity notification to group {group_chat_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending new activity notification to group {group_chat_id}: {e}")
        return False


async def send_activity_reminder_to_user(
    bot: Bot,
    user_telegram_id: int,
    activity_title: str,
    activity_date: datetime,
    location: str,
    is_registered: bool = True
) -> bool:
    """
    Send activity reminder to a single user (2 days before).

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location
        is_registered: Whether user is registered

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_activity_reminder_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            location=location,
            is_registered=is_registered
        )

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text
        )

        logger.info(f"Sent activity reminder to user {user_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending activity reminder to user {user_telegram_id}: {e}")
        return False


async def send_activity_reminder_to_group(
    bot: Bot,
    group_chat_id: int,
    activity_title: str,
    activity_date: datetime,
    participants_count: int,
    max_participants: Optional[int]
) -> bool:
    """
    Send activity reminder to Telegram group (2 days before).

    Args:
        bot: Telegram Bot instance
        group_chat_id: Telegram group chat ID
        activity_title: Activity title
        activity_date: Activity date and time
        participants_count: Current number of participants
        max_participants: Maximum participants

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_activity_reminder_group_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            participants_count=participants_count,
            max_participants=max_participants
        )

        await bot.send_message(
            chat_id=group_chat_id,
            text=message_text
        )

        logger.info(f"Sent activity reminder to group {group_chat_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending activity reminder to group {group_chat_id}: {e}")
        return False


def format_awaiting_confirmation_notification(
    activity_title: str,
    activity_date: datetime,
    location: str
) -> str:
    """
    Format awaiting confirmation notification.

    Sent after activity has passed, asking user to confirm attendance.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location

    Returns:
        Formatted message text
    """
    # Format date
    date_str = activity_date.strftime("%a, %d %b · %H:%M")

    message = (
        f"🏃 Тренировка завершена!\n\n"
        f"\"{activity_title}\"\n"
        f"{date_str} · {location}\n\n"
        f"Ты был на тренировке?"
    )

    return message


async def send_awaiting_confirmation_notification(
    bot: Bot,
    user_telegram_id: int,
    activity_id: str,
    activity_title: str,
    activity_date: datetime,
    location: str
) -> bool:
    """
    Send awaiting confirmation notification to user.

    Asks user to confirm whether they attended or missed the activity.
    Includes inline buttons for quick response.

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        activity_id: Activity ID (for callback data)
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        message_text = format_awaiting_confirmation_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            location=location
        )

        # Create inline buttons for confirmation (order matches web UI)
        keyboard = [[
            InlineKeyboardButton("Пропустил ✕", callback_data=f"confirm_missed_{activity_id}"),
            InlineKeyboardButton("Участвовал ✓", callback_data=f"confirm_attended_{activity_id}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text,
            reply_markup=reply_markup
        )

        logger.info(f"Sent awaiting confirmation notification to user {user_telegram_id} for activity {activity_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending awaiting confirmation notification to user {user_telegram_id}: {e}")
        return False


def format_activity_cancelled_notification(
    activity_title: str,
    activity_date: datetime,
    location: str,
    organizer_name: str
) -> str:
    """
    Format notification about activity cancellation.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location
        organizer_name: Name of the organizer who cancelled

    Returns:
        Formatted message text
    """
    date_str = activity_date.strftime("%d %B в %H:%M")

    message = (
        f"Тренировка отменена\n\n"
        f"{activity_title}\n"
        f"{date_str} · {location}\n\n"
        f"Организатор {organizer_name} отменил тренировку"
    )

    return message


async def send_activity_cancelled_notification(
    bot: Bot,
    user_telegram_id: int,
    activity_title: str,
    activity_date: datetime,
    location: str,
    organizer_name: str
) -> bool:
    """
    Send activity cancellation notification to a participant.

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location
        organizer_name: Name of the organizer

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_activity_cancelled_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            location=location,
            organizer_name=organizer_name
        )

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text
        )

        logger.info(f"Sent activity cancelled notification to user {user_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending activity cancelled notification to user {user_telegram_id}: {e}")
        return False


def format_activity_updated_notification(
    activity_title: str,
    changes_summary: str,
    webapp_link: str
) -> str:
    """
    Format notification about activity changes.

    Args:
        activity_title: Activity title
        changes_summary: Human-readable summary of changes
        webapp_link: Link to activity in webapp

    Returns:
        Formatted message text
    """
    message = (
        f"Тренировка изменена\n\n"
        f"{activity_title}\n\n"
        f"Изменения:\n{changes_summary}\n\n"
        f"[Подробнее]({webapp_link})"
    )

    return message


async def send_activity_updated_notification(
    bot: Bot,
    user_telegram_id: int,
    activity_title: str,
    changes_summary: str,
    webapp_link: str
) -> bool:
    """
    Send activity update notification to a participant.

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        activity_title: Activity title
        changes_summary: Human-readable summary of changes
        webapp_link: Link to activity in webapp

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_activity_updated_notification(
            activity_title=activity_title,
            changes_summary=changes_summary,
            webapp_link=webapp_link
        )

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

        logger.info(f"Sent activity updated notification to user {user_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending activity updated notification to user {user_telegram_id}: {e}")
        return False
