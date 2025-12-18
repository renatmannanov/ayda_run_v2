"""
Invitation Handler for Telegram Bot

Implements Flow 2A/2B: Invitations to clubs and groups
Handles deep links for joining clubs and groups.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from storage.user_storage import UserStorage
from storage.club_storage import ClubStorage
from storage.group_storage import GroupStorage
from storage.membership_storage import MembershipStorage
from config import settings
from bot.keyboards import (
    get_club_invitation_keyboard,
    get_group_invitation_keyboard,
    get_webapp_button,
    get_declined_invitation_keyboard
)
from bot.messages import (
    format_club_invitation_message,
    format_group_invitation_message,
    format_existing_user_club_invitation,
    format_existing_user_group_invitation,
    get_club_not_found_message,
    get_group_not_found_message,
    get_already_member_message,
    get_join_success_message,
    get_invitation_declined_message
)

logger = logging.getLogger(__name__)


async def handle_join_club(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle "Вступить" button click for club invitation.

    Callback data: "club_join_yes"
    """
    query = update.callback_query
    await query.answer()

    telegram_user = query.from_user
    club_id = context.user_data.get('invitation_id')

    if not club_id:
        logger.error(f"No club_id in context for user {telegram_user.id}")
        await query.edit_message_text("Произошла ошибка. Попробуй перейти по ссылке заново.")
        return

    try:
        # Get user from DB
        with UserStorage() as user_storage:
            user = user_storage.get_user_by_telegram_id(telegram_user.id)

            if not user:
                logger.error(f"User {telegram_user.id} not found in DB")
                await query.edit_message_text("Произошла ошибка. Попробуй /start")
                return

        # Check if already member
        with MembershipStorage() as membership_storage:
            if membership_storage.is_member_of_club(user.id, club_id):
                logger.info(f"User {telegram_user.id} already member of club {club_id}")
                await query.edit_message_text(get_already_member_message("клуба"))
                return

            # Add to club
            membership_storage.add_member_to_club(user.id, club_id)
            logger.info(f"User {telegram_user.id} joined club {club_id}")

        # Get club info
        with ClubStorage() as club_storage:
            club_data = club_storage.get_club_preview(club_id)

            if not club_data:
                await query.edit_message_text("Клуб не найден")
                return

            # Success message
            await query.edit_message_text(
                get_join_success_message(club_data['name'], "клуба")
            )

            # WebApp button with deep link to club
            webapp_url = f"{settings.app_url}?startapp=club_{club_id}"
            await query.message.reply_text(
                "Открой приложение:",
                reply_markup=get_webapp_button(webapp_url, f"🚀 Открыть {club_data['name']}")
            )

    except Exception as e:
        logger.error(f"Error joining club: {e}", exc_info=True)
        await query.edit_message_text("Произошла ошибка. Попробуй позже.")


async def handle_join_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle "Вступить" button click for group invitation.

    Callback data: "group_join_yes"
    """
    query = update.callback_query
    await query.answer()

    telegram_user = query.from_user
    group_id = context.user_data.get('invitation_id')

    if not group_id:
        logger.error(f"No group_id in context for user {telegram_user.id}")
        await query.edit_message_text("Произошла ошибка. Попробуй перейти по ссылке заново.")
        return

    try:
        # Get user from DB
        with UserStorage() as user_storage:
            user = user_storage.get_user_by_telegram_id(telegram_user.id)

            if not user:
                logger.error(f"User {telegram_user.id} not found in DB")
                await query.edit_message_text("Произошла ошибка. Попробуй /start")
                return

        # Check if already member
        with MembershipStorage() as membership_storage:
            if membership_storage.is_member_of_group(user.id, group_id):
                logger.info(f"User {telegram_user.id} already member of group {group_id}")
                await query.edit_message_text(get_already_member_message("группы"))
                return

            # Add to group
            membership_storage.add_member_to_group(user.id, group_id)
            logger.info(f"User {telegram_user.id} joined group {group_id}")

        # Get group info
        with GroupStorage() as group_storage:
            group_data = group_storage.get_group_preview(group_id)

            if not group_data:
                await query.edit_message_text("Группа не найдена")
                return

            # Success message
            await query.edit_message_text(
                get_join_success_message(group_data['name'], "группы")
            )

            # WebApp button with deep link to group
            webapp_url = f"{settings.app_url}?startapp=group_{group_id}"
            await query.message.reply_text(
                "Открой приложение:",
                reply_markup=get_webapp_button(webapp_url, f"🚀 Открыть {group_data['name']}")
            )

    except Exception as e:
        logger.error(f"Error joining group: {e}", exc_info=True)
        await query.edit_message_text("Произошла ошибка. Попробуй позже.")


async def handle_decline_invitation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle "Не сейчас" button click for invitations.

    Callback data: "club_join_no" or "group_join_no"
    """
    query = update.callback_query
    await query.answer()

    logger.info(f"User {query.from_user.id} declined invitation")

    await query.edit_message_text(get_invitation_declined_message())

    # Show "Explore activities" button
    await query.message.reply_text(
        "Открой приложение:",
        reply_markup=get_webapp_button(settings.app_url, "🔍 Посмотреть тренировки")
    )


async def handle_explore_activities(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle "Посмотреть тренировки" button.

    Callback data: "explore_activities"
    """
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("Открываю приложение...")

    # Open webapp
    await query.message.reply_text(
        "Найди ближайшую тренировку:",
        reply_markup=get_webapp_button(settings.app_url)
    )


# Callback query handlers for invitations
join_invitation_handlers = [
    CallbackQueryHandler(handle_join_club, pattern="^club_join_yes$"),
    CallbackQueryHandler(handle_join_group, pattern="^group_join_yes$"),
    CallbackQueryHandler(handle_decline_invitation, pattern="^(club|group)_join_no$"),
    CallbackQueryHandler(handle_explore_activities, pattern="^explore_activities$"),
]
