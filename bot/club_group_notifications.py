"""
Club and Group deletion notifications.

Sends Telegram notifications to members when clubs or groups are deleted.
"""
from telegram import Bot
from telegram.error import TelegramError
import logging

logger = logging.getLogger(__name__)


def format_club_deleted_notification(
    club_name: str,
    admin_name: str,
    activities_deleted: bool = True
) -> str:
    """
    Format notification about club deletion.

    Args:
        club_name: Name of the deleted club
        admin_name: Name of the admin who deleted the club
        activities_deleted: Whether activities were deleted or kept

    Returns:
        Formatted message text
    """
    if activities_deleted:
        return (
            f"Клуб удалён\n\n"
            f"Клуб «{club_name}» был удалён администратором {admin_name}.\n\n"
            f"Все группы и тренировки клуба также удалены."
        )
    return (
        f"Клуб удалён\n\n"
        f"Клуб «{club_name}» был удалён администратором {admin_name}.\n\n"
        f"Тренировки сохранены и теперь принадлежат их создателям."
    )


async def send_club_deleted_notification(
    bot: Bot,
    user_telegram_id: int,
    club_name: str,
    admin_name: str,
    activities_deleted: bool = True
) -> bool:
    """
    Send club deletion notification to a member.

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        club_name: Name of the deleted club
        admin_name: Name of the admin who deleted
        activities_deleted: Whether activities were deleted

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message = format_club_deleted_notification(
            club_name=club_name,
            admin_name=admin_name,
            activities_deleted=activities_deleted
        )

        await bot.send_message(chat_id=user_telegram_id, text=message)
        logger.info(f"Sent club deleted notification to user {user_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending club deleted notification to user {user_telegram_id}: {e}")
        return False


def format_group_deleted_notification(
    group_name: str,
    admin_name: str,
    club_name: str = None,
    activities_deleted: bool = True
) -> str:
    """
    Format notification about group deletion.

    Args:
        group_name: Name of the deleted group
        admin_name: Name of the admin who deleted
        club_name: Name of the parent club (if any)
        activities_deleted: Whether activities were deleted or kept

    Returns:
        Formatted message text
    """
    if club_name:
        base = f"Группа «{group_name}» клуба «{club_name}» была удалена."
    else:
        base = f"Группа «{group_name}» была удалена администратором {admin_name}."

    if activities_deleted:
        return f"Группа удалена\n\n{base}\n\nТренировки группы также удалены."
    return f"Группа удалена\n\n{base}\n\nТренировки сохранены и принадлежат их создателям."


async def send_group_deleted_notification(
    bot: Bot,
    user_telegram_id: int,
    group_name: str,
    admin_name: str,
    club_name: str = None,
    activities_deleted: bool = True
) -> bool:
    """
    Send group deletion notification to a member.

    Args:
        bot: Telegram Bot instance
        user_telegram_id: User's Telegram ID
        group_name: Name of the deleted group
        admin_name: Name of the admin who deleted
        club_name: Name of the parent club (if any)
        activities_deleted: Whether activities were deleted

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        message = format_group_deleted_notification(
            group_name=group_name,
            admin_name=admin_name,
            club_name=club_name,
            activities_deleted=activities_deleted
        )

        await bot.send_message(chat_id=user_telegram_id, text=message)
        logger.info(f"Sent group deleted notification to user {user_telegram_id}")
        return True

    except TelegramError as e:
        logger.error(f"Error sending group deleted notification to user {user_telegram_id}: {e}")
        return False
