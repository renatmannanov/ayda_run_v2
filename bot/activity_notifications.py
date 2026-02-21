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
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.error import TelegramError
from app.core.timezone import format_datetime_local, get_weekday_accusative

logger = logging.getLogger(__name__)

# Sport type icons (must match SportType enum in schemas/common.py)
SPORT_ICONS = {
    'running': '🏃',
    'trail': '⛰️',
    'hiking': '🥾',
    'cycling': '🚴',
    'yoga': '🧘',
    'workout': '💪',
    'other': '🏅',
}


def get_sport_icon(sport_type: str) -> str:
    """Get emoji icon for sport type."""
    if not sport_type:
        return '🏅'
    return SPORT_ICONS.get(sport_type.lower(), '🏅')


def format_participants_line(names: List[str]) -> str:
    """
    Format participants line: 'Идут: Алексей, Мария, Иван, Петр, Анна + 3'

    Args:
        names: List of participant first names

    Returns:
        Formatted string or empty string if no participants
    """
    if not names:
        return ""
    if len(names) <= 5:
        return f"Идут: {', '.join(names)}"
    else:
        return f"Идут: {', '.join(names[:5])} + {len(names) - 5}"


def format_new_activity_notification(
    activity_title: str,
    activity_date: datetime,
    location: str,
    entity_name: str,
    sport_type: str = None,
    participant_names: List[str] = None,
    country: str = None,
    city: str = None
) -> str:
    """
    Format notification message for new activity.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        location: Activity location
        entity_name: Club/Group name
        sport_type: Sport type for icon (running, trail, etc.)
        participant_names: List of participant first names
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        Formatted message text
    """
    # Get weekday for header ("в субботу", "в среду")
    weekday_str = get_weekday_accusative(activity_date, country, city)

    # Format date: "Сб, 25 января · 07:30"
    date_str = format_datetime_local(activity_date, country, city, "%a, %d %B · %H:%M")

    # Get sport icon
    sport_icon = get_sport_icon(sport_type)

    # Build message
    lines = [
        f"{entity_name} · Тренировка {weekday_str}",
        "",
        f"{sport_icon} {activity_title}",
        date_str,
        f"📍 {location}",
    ]

    # Add participants if any
    participants_line = format_participants_line(participant_names or [])
    if participants_line:
        lines.append("")
        lines.append(participants_line)

    return "\n".join(lines)


def format_new_activity_group_notification(
    activity_title: str,
    activity_date: datetime,
    location: str,
    entity_name: str,
    sport_type: str = None,
    participant_names: List[str] = None,
    country: str = None,
    city: str = None
) -> str:
    """
    Format notification message for Telegram group posting.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        location: Activity location
        entity_name: Club/Group name
        sport_type: Sport type for icon (running, trail, etc.)
        participant_names: List of participant first names
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        Formatted message text for group
    """
    # Get weekday for header ("в субботу", "в среду")
    weekday_str = get_weekday_accusative(activity_date, country, city)

    # Format date: "Сб, 25 января · 07:30"
    date_str = format_datetime_local(activity_date, country, city, "%a, %d %B · %H:%M")

    # Get sport icon
    sport_icon = get_sport_icon(sport_type)

    # Build message (same format as DM, with club name)
    lines = [
        f"{entity_name} · Тренировка {weekday_str}",
        "",
        f"{sport_icon} {activity_title}",
        date_str,
        f"📍 {location}",
    ]

    # Add participants if any
    participants_line = format_participants_line(participant_names or [])
    if participants_line:
        lines.append("")
        lines.append(participants_line)

    return "\n".join(lines)


def format_activity_reminder_notification(
    activity_title: str,
    activity_date: datetime,
    location: str,
    sport_type: str = None,
    is_registered: bool = True,
    country: str = None,
    city: str = None
) -> str:
    """
    Format reminder notification (2 days before activity).

    Args:
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        location: Activity location
        sport_type: Sport type for icon
        is_registered: Whether user is registered for activity
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        Formatted message text
    """
    # Format date: "Вт, 21 января · 06:45"
    date_str = format_datetime_local(activity_date, country, city, "%a, %d %B · %H:%M")

    # Get sport icon
    sport_icon = get_sport_icon(sport_type)

    lines = [
        "Напоминание",
        "",
        f"{sport_icon} {activity_title}",
        date_str,
        f"📍 {location}",
    ]

    if is_registered:
        lines.append("")
        lines.append("Ждём на тренировке ✓")

    return "\n".join(lines)


def format_activity_reminder_group_notification(
    activity_title: str,
    activity_date: datetime,
    location: str,
    sport_type: str = None,
    participant_names: List[str] = None,
    country: str = None,
    city: str = None
) -> str:
    """
    Format reminder notification for Telegram group.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        location: Activity location
        sport_type: Sport type for icon
        participant_names: List of participant first names
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        Formatted message text for group
    """
    # Format date: "Вт, 21 января · 19:00"
    date_str = format_datetime_local(activity_date, country, city, "%a, %d %B · %H:%M")

    # Get sport icon
    sport_icon = get_sport_icon(sport_type)

    lines = [
        "Через 2 дня",
        "",
        f"{sport_icon} {activity_title}",
        date_str,
        f"📍 {location}",
    ]

    # Add participants if any
    participants_line = format_participants_line(participant_names or [])
    if participants_line:
        lines.append("")
        lines.append(participants_line)

    return "\n".join(lines)


async def send_new_activity_notification_to_user(
    bot: Bot,
    user_telegram_id: int,
    activity_title: str,
    activity_date: datetime,
    location: str,
    entity_name: str,
    webapp_link: str,
    sport_type: str = None,
    participant_names: List[str] = None,
    country: str = None,
    city: str = None
) -> bool:
    """
    Send new activity notification to a single user.

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location
        entity_name: Club/Group name
        webapp_link: Link to activity in webapp
        sport_type: Sport type for icon
        participant_names: List of participant first names
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_new_activity_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            location=location,
            entity_name=entity_name,
            sport_type=sport_type,
            participant_names=participant_names,
            country=country,
            city=city
        )

        # Button text depends on participants
        button_text = "Присоединиться" if participant_names else "Записаться"
        keyboard = [[InlineKeyboardButton(button_text, web_app=WebAppInfo(url=webapp_link))]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
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
    entity_name: str,
    webapp_link: str,
    sport_type: str = None,
    participant_names: List[str] = None,
    country: str = None,
    city: str = None
) -> bool:
    """
    Send new activity notification to Telegram group.

    Args:
        bot: Telegram Bot instance
        group_chat_id: Telegram group chat ID
        activity_title: Activity title
        activity_date: Activity date and time
        location: Activity location
        entity_name: Club/Group name
        webapp_link: Link to activity in webapp
        sport_type: Sport type for icon
        participant_names: List of participant first names
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_new_activity_group_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            location=location,
            entity_name=entity_name,
            sport_type=sport_type,
            participant_names=participant_names,
            country=country,
            city=city
        )

        # Button text depends on participants
        # Note: WebAppInfo doesn't work in group chats, use url= with Telegram deep link
        button_text = "Присоединиться" if participant_names else "Записаться"
        keyboard = [[InlineKeyboardButton(button_text, url=webapp_link)]]
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
    webapp_link: str,
    sport_type: str = None,
    is_registered: bool = True,
    country: str = None,
    city: str = None
) -> bool:
    """
    Send activity reminder to a single user (2 days before).

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        location: Activity location
        webapp_link: Link to activity in webapp
        sport_type: Sport type for icon
        is_registered: Whether user is registered
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_activity_reminder_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            location=location,
            sport_type=sport_type,
            is_registered=is_registered,
            country=country,
            city=city
        )

        # Button to view details and track
        keyboard = [[InlineKeyboardButton("Посмотреть детали и трек", web_app=WebAppInfo(url=webapp_link))]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
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
    location: str,
    webapp_link: str,
    sport_type: str = None,
    participant_names: List[str] = None,
    country: str = None,
    city: str = None
) -> bool:
    """
    Send activity reminder to Telegram group (2 days before).

    Args:
        bot: Telegram Bot instance
        group_chat_id: Telegram group chat ID
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        location: Activity location
        webapp_link: Link to activity in webapp
        sport_type: Sport type for icon
        participant_names: List of participant first names
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_activity_reminder_group_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            location=location,
            sport_type=sport_type,
            participant_names=participant_names,
            country=country,
            city=city
        )

        # Button to join
        # Note: WebAppInfo doesn't work in group chats, use url= with Telegram deep link
        keyboard = [[InlineKeyboardButton("Присоединиться", url=webapp_link)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(
            chat_id=group_chat_id,
            text=message_text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

        logger.info(f"Sent activity reminder to group {group_chat_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending activity reminder to group {group_chat_id}: {e}")
        return False


def format_awaiting_confirmation_notification(
    activity_title: str,
    activity_date: datetime,
    location: str,
    country: str = None,
    city: str = None
) -> str:
    """
    Format awaiting confirmation notification.

    Sent after activity has passed, asking user to confirm attendance.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        location: Activity location
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        Formatted message text
    """
    # Format date in local timezone
    date_str = format_datetime_local(activity_date, country, city, "%a, %d %b · %H:%M")

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
    location: str,
    country: str = None,
    city: str = None
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
        activity_date: Activity date and time (UTC)
        location: Activity location
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        message_text = format_awaiting_confirmation_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            location=location,
            country=country,
            city=city
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


# ============================================================================
# Post-Training Link Collection Notifications
# ============================================================================

def format_post_training_notification(
    activity_title: str,
    activity_date: datetime,
    location: str,
    country: str = None,
    city: str = None
) -> str:
    """
    Format post-training notification asking for training link.

    Sent after activity has passed to club/group participants.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        location: Activity location
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        Formatted message text
    """
    date_str = format_datetime_local(activity_date, country, city, "%a, %d %b · %H:%M")

    message = (
        f"✅ Тренировка «{activity_title}» завершена.\n\n"
        f"{date_str} · {location}\n\n"
        f"Отправь ссылку на тренировку ответным сообщением "
        f"(Strava, Garmin, Coros, Suunto, Polar). "
        f"И мы перешлём её твоему тренеру для анализа."
        f"\n\nИли подключи Strava /connect_strava, чтобы синкать и отправлять автоматически."
    )

    return message


async def send_trainer_link_notification(
    bot: Bot,
    trainer_telegram_id: int,
    participant_name: str,
    activity_title: str,
    training_link: str
) -> bool:
    """
    Notify trainer when participant submits training link.

    Real-time notification sent immediately when user sends a link.

    Args:
        bot: Telegram Bot instance
        trainer_telegram_id: Trainer's Telegram ID
        participant_name: Name of participant who submitted link
        activity_title: Activity title
        training_link: URL to the training record

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message = (
            f"▪️ {participant_name} отправил ссылку на тренировку «{activity_title}»\n"
            f"{training_link}"
        )

        await bot.send_message(
            chat_id=trainer_telegram_id,
            text=message,
            disable_web_page_preview=True
        )

        logger.info(f"Sent trainer link notification to {trainer_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending trainer link notification to {trainer_telegram_id}: {e}")
        return False


async def send_post_training_notification(
    bot: Bot,
    user_telegram_id: int,
    activity_id: str,
    activity_title: str,
    activity_date: datetime,
    location: str,
    country: str = None,
    city: str = None
) -> bool:
    """
    Send post-training notification asking for training link.

    For club/group activities - asks participants to send training link.
    Includes buttons for "will send later" and "wasn't there".

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        activity_id: Activity ID (for callback data)
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        location: Activity location
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message_text = format_post_training_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            location=location,
            country=country,
            city=city
        )

        keyboard = [[
            InlineKeyboardButton("Отправлю позже", callback_data=f"post_training_later_{activity_id}"),
            InlineKeyboardButton("Не был(а)", callback_data=f"post_training_missed_{activity_id}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(
            chat_id=user_telegram_id,
            text=message_text,
            reply_markup=reply_markup
        )

        logger.info(f"Sent post-training notification to user {user_telegram_id} for activity {activity_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending post-training notification to user {user_telegram_id}: {e}")
        return False


def format_activity_cancelled_notification(
    activity_title: str,
    activity_date: datetime,
    location: str,
    organizer_name: str,
    country: str = None,
    city: str = None
) -> str:
    """
    Format notification about activity cancellation.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        location: Activity location
        organizer_name: Name of the organizer who cancelled
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        Formatted message text
    """
    date_str = format_datetime_local(activity_date, country, city, "%d %B в %H:%M")

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


# ============================================================================
# Organizer Attendance Check Notification
# ============================================================================

def format_organizer_checkin_notification(
    activity_title: str,
    activity_date: datetime,
    participants_count: int,
    webapp_link: str,
    country: str = None,
    city: str = None
) -> str:
    """
    Format notification for organizer to mark attendance.

    Sent after activity has passed, asking organizer to confirm attendees.

    Args:
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        participants_count: Number of registered participants
        webapp_link: Link to activity in webapp
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        Formatted message text
    """
    date_str = format_datetime_local(activity_date, country, city, "%a, %d %b")

    message = (
        f"📋 Тренировка завершена!\n\n"
        f"\"{activity_title}\"\n"
        f"{date_str} · {participants_count} участников\n\n"
        f"Давай отметим, кто был на тренировке — "
        f"это поможет вести статистику посещений и понимать активность участников."
    )

    return message


async def send_organizer_checkin_notification(
    bot: Bot,
    organizer_telegram_id: int,
    activity_id: str,
    activity_title: str,
    activity_date: datetime,
    participants_count: int,
    webapp_link: str,
    country: str = None,
    city: str = None
) -> bool:
    """
    Send notification to organizer to mark attendance.

    Shows button to open attendance marking in webapp.
    Only sent for club/group activities.

    Args:
        bot: Telegram Bot instance
        organizer_telegram_id: Organizer's Telegram ID
        activity_id: Activity ID (for callback data)
        activity_title: Activity title
        activity_date: Activity date and time (UTC)
        participants_count: Number of registered participants
        webapp_link: Link to activity in webapp
        country: Country for timezone conversion
        city: City for timezone conversion

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        message_text = format_organizer_checkin_notification(
            activity_title=activity_title,
            activity_date=activity_date,
            participants_count=participants_count,
            webapp_link=webapp_link,
            country=country,
            city=city
        )

        # Create inline button to open webapp
        keyboard = [[
            InlineKeyboardButton("Отметить посещение 📋", web_app=WebAppInfo(url=webapp_link))
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(
            chat_id=organizer_telegram_id,
            text=message_text,
            reply_markup=reply_markup
        )

        logger.info(f"Sent organizer checkin notification to {organizer_telegram_id} for activity {activity_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending organizer checkin notification to {organizer_telegram_id}: {e}")
        return False
