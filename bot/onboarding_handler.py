"""
Onboarding Handler for Telegram Bot

Implements Flow 1: Participant - self-registration
Handles new user onboarding process with sports selection and app intro.
"""

import logging
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from storage.user_storage import UserStorage
from config import settings
from bot.keyboards import (
    get_consent_keyboard,
    get_sports_selection_keyboard,
    get_role_selection_keyboard,
    get_intro_done_keyboard,
    get_webapp_button
)
from bot.messages import (
    get_welcome_message,
    get_consent_declined_message,
    get_sports_selection_message,
    get_role_selection_message,
    get_intro_message,
    get_completion_message,
    get_returning_user_message,
    get_onboarding_cancelled_message
)

logger = logging.getLogger(__name__)

# Conversation states
AWAITING_CONSENT = 1
SELECTING_SPORTS = 2
SELECTING_ROLE = 3
SHOWING_INTRO = 4


async def start_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point for /start command (without parameters).

    Checks if user exists and has completed onboarding.
    If not, starts onboarding flow.
    """
    telegram_user = update.effective_user

    logger.info(f"User {telegram_user.id} (@{telegram_user.username}) started onboarding")

    # Get or create user
    with UserStorage() as user_storage:
        user = user_storage.get_or_create_user(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name
        )

        # Check if user already completed onboarding
        if user.has_completed_onboarding:
            logger.info(f"User {telegram_user.id} already completed onboarding")
            await update.message.reply_text(
                get_returning_user_message(user.first_name)
            )
            # Show webapp button
            await update.message.reply_text(
                "Открой приложение:",
                reply_markup=get_webapp_button(settings.app_url)
            )
            return ConversationHandler.END

    # Start onboarding - show welcome message with consent request
    await update.message.reply_text(
        get_welcome_message(telegram_user.first_name),
        reply_markup=get_consent_keyboard()
    )

    return AWAITING_CONSENT


async def handle_consent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle user consent to use Telegram data.

    Callback data: "consent_yes" or "consent_no"
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "consent_no":
        # User declined consent
        logger.info(f"User {query.from_user.id} declined consent")
        await query.edit_message_text(get_consent_declined_message())
        return ConversationHandler.END

    # User accepted consent - show sports selection
    logger.info(f"User {query.from_user.id} accepted consent")

    # Initialize selected sports in context
    context.user_data['selected_sports'] = []

    await query.edit_message_text(
        get_sports_selection_message(),
        reply_markup=get_sports_selection_keyboard([])
    )

    return SELECTING_SPORTS


async def handle_sports_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle sports selection (multi-select).

    Callback data:
    - "sport_toggle_RUNNING" - toggle sport
    - "sport_done" - finish selection
    - "sport_skip" - skip selection
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    selected_sports = context.user_data.get('selected_sports', [])

    if callback_data.startswith('sport_toggle_'):
        # Toggle sport selection
        sport_id = callback_data.replace('sport_toggle_', '')

        if sport_id in selected_sports:
            selected_sports.remove(sport_id)
            logger.info(f"User {query.from_user.id} deselected sport: {sport_id}")
        else:
            selected_sports.append(sport_id)
            logger.info(f"User {query.from_user.id} selected sport: {sport_id}")

        context.user_data['selected_sports'] = selected_sports

        # Update keyboard with new selection
        await query.edit_message_reply_markup(
            reply_markup=get_sports_selection_keyboard(selected_sports)
        )

        return SELECTING_SPORTS

    elif callback_data == 'sport_done' or callback_data == 'sport_skip':
        # Save selected sports to database
        telegram_user = query.from_user

        if callback_data == 'sport_skip':
            logger.info(f"User {telegram_user.id} skipped sports selection")
            selected_sports = []
        else:
            logger.info(f"User {telegram_user.id} completed sports selection: {selected_sports}")

        with UserStorage() as user_storage:
            user = user_storage.get_user_by_telegram_id(telegram_user.id)
            if user:
                user_storage.update_preferred_sports(user.id, selected_sports)

        # Show role selection
        await query.edit_message_text(
            get_role_selection_message(),
            reply_markup=get_role_selection_keyboard()
        )

        return SELECTING_ROLE

    return SELECTING_SPORTS


async def handle_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle role selection.

    Callback data: "role_participant" or "role_organizer"
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    telegram_user = query.from_user

    if callback_data == "role_participant":
        # User is a participant - show app intro
        logger.info(f"User {telegram_user.id} selected role: participant")

        await query.edit_message_text(
            get_intro_message(),
            reply_markup=get_intro_done_keyboard()
        )

        return SHOWING_INTRO

    elif callback_data == "role_organizer":
        # User is an organizer
        logger.info(f"User {telegram_user.id} selected role: organizer")

        # TODO: Implement organizer flow (Phase 3)
        await query.edit_message_text(
            "Функция для организаторов будет доступна скоро!\n\n"
            "А пока можешь использовать приложение как участник:"
        )

        telegram_user = query.from_user

        # Mark onboarding as complete
        with UserStorage() as user_storage:
            user = user_storage.get_user_by_telegram_id(telegram_user.id)
            if user:
                user_storage.mark_onboarding_complete(user.id)

        await query.message.reply_text(
            "Открой приложение:",
            reply_markup=get_webapp_button(settings.app_url)
        )

        return ConversationHandler.END

    return SELECTING_ROLE


async def complete_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Complete onboarding flow.

    Mark user as onboarded and show completion message with WebApp button.
    """
    query = update.callback_query
    await query.answer()

    telegram_user = query.from_user

    # Mark onboarding as complete
    with UserStorage() as user_storage:
        user = user_storage.get_user_by_telegram_id(telegram_user.id)
        if user:
            user_storage.mark_onboarding_complete(user.id)
            logger.info(f"User {telegram_user.id} completed onboarding")

            # Show completion message
            await query.edit_message_text(
                get_completion_message(user.first_name, user.username)
            )

            # Show WebApp button
            await query.message.reply_text(
                "Открой приложение:",
                reply_markup=get_webapp_button(settings.app_url)
            )

    return ConversationHandler.END


async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel onboarding (timeout or /cancel command).
    """
    if update.message:
        telegram_user = update.message.from_user
        await update.message.reply_text(get_onboarding_cancelled_message())
    else:
        telegram_user = update.callback_query.from_user

    logger.info(f"User {telegram_user.id} cancelled onboarding")

    # Clear user data
    context.user_data.clear()

    return ConversationHandler.END


# ConversationHandler for onboarding
onboarding_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", start_onboarding)
    ],
    states={
        AWAITING_CONSENT: [
            CallbackQueryHandler(handle_consent, pattern="^consent_")
        ],
        SELECTING_SPORTS: [
            CallbackQueryHandler(handle_sports_selection, pattern="^sport_")
        ],
        SELECTING_ROLE: [
            CallbackQueryHandler(handle_role_selection, pattern="^role_")
        ],
        SHOWING_INTRO: [
            CallbackQueryHandler(complete_onboarding, pattern="^intro_done$")
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_onboarding)
    ],
    conversation_timeout=300,  # 5 minutes timeout
)
