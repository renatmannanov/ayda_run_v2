"""
Onboarding Handler for Telegram Bot

Implements Flow 1: Participant - self-registration
Handles new user onboarding process with sports selection and app intro.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from storage.user_storage import UserStorage
from storage.club_storage import ClubStorage
from storage.group_storage import GroupStorage
from storage.membership_storage import MembershipStorage
from config import settings
from bot.keyboards import (
    get_consent_keyboard,
    get_photo_visibility_keyboard,
    get_sports_selection_keyboard,
    get_role_selection_keyboard,
    get_intro_done_keyboard,
    get_webapp_button,
    get_club_invitation_keyboard,
    get_group_invitation_keyboard
)
from bot.messages import (
    get_welcome_message,
    get_consent_declined_message,
    get_photo_visibility_message,
    get_sports_selection_message,
    get_role_selection_message,
    get_intro_message,
    get_completion_message,
    get_returning_user_message,
    get_onboarding_cancelled_message,
    format_club_invitation_message,
    format_group_invitation_message,
    format_existing_user_club_invitation,
    format_existing_user_group_invitation,
    get_club_not_found_message,
    get_group_not_found_message,
    get_join_success_message
)
from bot.analytics import track_onboarding_step, track_onboarding_complete

logger = logging.getLogger(__name__)

# Conversation states
AWAITING_CONSENT = 1
ASKING_PHOTO_VISIBILITY = 6
SELECTING_SPORTS = 2
SELECTING_ROLE = 3
ASKING_STRAVA = 4
SHOWING_INTRO = 5


async def handle_join_from_group(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                  user, chat_id_str: str) -> int:
    """
    Handle /start join_{chat_id} - registration from group button.

    Automatically adds user to the club associated with the Telegram group.
    """
    from storage.db import MembershipSource, MembershipStatus
    from bot.cache import add_member_to_cache

    try:
        chat_id = int(chat_id_str)
    except ValueError:
        await update.message.reply_text("Неверная ссылка.")
        return ConversationHandler.END

    # Find club by chat_id
    with ClubStorage() as cs:
        club = cs.get_club_by_telegram_chat_id(chat_id)
        if not club:
            await update.message.reply_text(
                "❌ Эта группа не связана с клубом в Ayda Run.\n\n"
                "Попросите организатора создать клуб командой /create_club"
            )
            return ConversationHandler.END

    # Check if already member and handle activation
    with MembershipStorage() as ms:
        existing = ms.get_membership(user.id, club.id)

        if existing:
            if existing.status == MembershipStatus.ACTIVE:
                # Already active - just show welcome
                await update.message.reply_text(
                    f"👋 Ты уже участник клуба «{club.name}»!\n\n"
                    "Открой приложение, чтобы посмотреть расписание."
                )
                webapp_url = f"{settings.app_url}?startapp=club_{club.id}"
                await update.message.reply_text(
                    "Открой приложение:",
                    reply_markup=get_webapp_button(webapp_url, f"🚀 Открыть {club.name}")
                )
                return ConversationHandler.END
            else:
                # PENDING or other status - activate via deep link
                ms.add_member_to_club_with_source(
                    user_id=user.id,
                    club_id=club.id,
                    source=MembershipSource.DEEP_LINK,
                    status=MembershipStatus.ACTIVE
                )
                logger.info(f"Activated pending member {user.id} in club {club.id} via deep link")
        else:
            # New member - add to club
            ms.add_member_to_club_with_source(
                user_id=user.id,
                club_id=club.id,
                source=MembershipSource.DEEP_LINK,
                status=MembershipStatus.ACTIVE
            )

    # Add to cache
    add_member_to_cache(chat_id, update.effective_user.id)

    logger.info(f"User {user.id} joined club {club.id} via deep link")

    await update.message.reply_text(
        f"🎉 Добро пожаловать в клуб «{club.name}»!\n\n"
        f"Теперь ты можешь:\n"
        f"▪️ Смотреть расписание тренировок\n"
        f"▪️ Записываться на мероприятия\n"
        f"▪️ Общаться с участниками"
    )

    webapp_url = f"{settings.app_url}?startapp=club_{club.id}"
    await update.message.reply_text(
        "Открой приложение:",
        reply_markup=get_webapp_button(webapp_url, f"🚀 Открыть {club.name}")
    )

    return ConversationHandler.END


async def handle_existing_user_invitation(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                          user, invitation_type: str, invitation_id: str) -> int:
    """
    Handle invitation for existing user who already completed onboarding.

    Shows short flow: Welcome back + entity info + Join/Decline buttons.
    Supports: club, group, join (from group registration button), activity (deep link to activity)
    """
    try:
        # Handle "join" deep link (from group registration button)
        if invitation_type == "join":
            return await handle_join_from_group(update, context, user, invitation_id)

        # Handle "activity" deep link - just open webapp with activity
        if invitation_type == "activity":
            webapp_url = f"{settings.app_url}?startapp=activity_{invitation_id}"
            await update.message.reply_text(
                "📋 Открываю тренировку...",
                reply_markup=get_webapp_button(webapp_url, "🚀 Открыть тренировку")
            )
            return ConversationHandler.END

        if invitation_type == "club":
            with ClubStorage() as club_storage:
                club_data = club_storage.get_club_preview(invitation_id)

                if not club_data:
                    await update.message.reply_text(get_club_not_found_message())
                    return ConversationHandler.END

                # Check if already member
                with MembershipStorage() as membership_storage:
                    if membership_storage.is_member_of_club(user.id, invitation_id):
                        await update.message.reply_text(
                            f"👋 Ты уже участник клуба {club_data['name']}!\n\n"
                            "Открой приложение, чтобы посмотреть расписание тренировок."
                        )
                        webapp_url = f"{settings.app_url}?startapp=club_{invitation_id}"
                        await update.message.reply_text(
                            "Открой приложение:",
                            reply_markup=get_webapp_button(webapp_url, f"🚀 Открыть {club_data['name']}")
                        )
                        return ConversationHandler.END

                # Show invitation
                message = format_existing_user_club_invitation(user.first_name, club_data)
                await update.message.reply_text(
                    message,
                    reply_markup=get_club_invitation_keyboard(is_existing_user=True)
                )

        else:  # group
            with GroupStorage() as group_storage:
                group_data = group_storage.get_group_preview(invitation_id)

                if not group_data:
                    await update.message.reply_text(get_group_not_found_message())
                    return ConversationHandler.END

                # Check if already member
                with MembershipStorage() as membership_storage:
                    if membership_storage.is_member_of_group(user.id, invitation_id):
                        await update.message.reply_text(
                            f"👋 Ты уже участник группы {group_data['name']}!\n\n"
                            "Открой приложение, чтобы посмотреть расписание тренировок."
                        )
                        webapp_url = f"{settings.app_url}?startapp=group_{invitation_id}"
                        await update.message.reply_text(
                            "Открой приложение:",
                            reply_markup=get_webapp_button(webapp_url, f"🚀 Открыть {group_data['name']}")
                        )
                        return ConversationHandler.END

                # Show invitation
                message = format_existing_user_group_invitation(user.first_name, group_data)
                await update.message.reply_text(
                    message,
                    reply_markup=get_group_invitation_keyboard(is_existing_user=True)
                )

        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error handling existing user invitation: {e}", exc_info=True)
        await update.message.reply_text("Произошла ошибка. Попробуй позже.")
        return ConversationHandler.END


async def start_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point for /start command.

    Supports deep links:
    - /start club_UUID - invitation to club
    - /start group_UUID - invitation to group

    Checks if user exists and has completed onboarding.
    If not, starts onboarding flow.
    """
    telegram_user = update.effective_user

    # Parse deep link parameters
    invitation_type = None
    invitation_id = None

    if context.args and len(context.args) > 0:
        param = context.args[0]
        if param.startswith("club_"):
            invitation_type = "club"
            invitation_id = param[5:]  # Remove "club_" prefix
            logger.info(f"User {telegram_user.id} clicked club invitation: {invitation_id}")
        elif param.startswith("group_"):
            invitation_type = "group"
            invitation_id = param[6:]  # Remove "group_" prefix
            logger.info(f"User {telegram_user.id} clicked group invitation: {invitation_id}")
        elif param.startswith("join_"):
            # Deep link from group registration button
            invitation_type = "join"
            invitation_id = param[5:]  # This is chat_id
            logger.info(f"User {telegram_user.id} clicked join deep link for chat: {invitation_id}")
        elif param.startswith("activity_"):
            # Deep link to activity (e.g., from checkin notification)
            invitation_type = "activity"
            invitation_id = param[9:]  # Remove "activity_" prefix
            logger.info(f"User {telegram_user.id} clicked activity deep link: {invitation_id}")

    # Store invitation info in context
    if invitation_type:
        context.user_data['invitation_type'] = invitation_type
        context.user_data['invitation_id'] = invitation_id

    logger.info(f"User {telegram_user.id} (@{telegram_user.username}) started onboarding")

    # Get or create user
    with UserStorage() as user_storage:
        user = user_storage.get_or_create_user(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name
        )

        # Save Telegram profile photo if available and not already saved
        if not user.photo:
            try:
                # Get the largest photo size
                photo_file = await telegram_user.get_profile_photos(limit=1)
                if photo_file.total_count > 0:
                    # Get file_id from the largest photo
                    largest_photo = photo_file.photos[0][-1]  # Last element is largest
                    user_storage.update_photo(user.id, largest_photo.file_id)
                    logger.info(f"Saved Telegram photo for user {telegram_user.id}")
            except Exception as e:
                logger.error(f"Error saving Telegram photo: {e}")
                # Continue without photo - not critical

        # Check if user already completed onboarding
        if user.has_completed_onboarding:
            logger.info(f"User {telegram_user.id} already completed onboarding")

            # If has invitation - show invitation flow for existing user
            if invitation_type:
                return await handle_existing_user_invitation(update, context, user, invitation_type, invitation_id)

            # No invitation - show regular welcome back
            await update.message.reply_text(
                get_returning_user_message(user.first_name)
            )
            # Show webapp button
            await update.message.reply_text(
                "Открой приложение:",
                reply_markup=get_webapp_button(settings.app_url)
            )
            return ConversationHandler.END

    # Start onboarding
    # If has invitation - show combined message (invitation + app intro)
    if invitation_type:
        try:
            if invitation_type == "club":
                with ClubStorage() as club_storage:
                    entity_data = club_storage.get_club_preview(invitation_id)
                    if not entity_data:
                        await update.message.reply_text(get_club_not_found_message())
                        return ConversationHandler.END
                    message = format_club_invitation_message(telegram_user.first_name, entity_data)
            else:  # group
                with GroupStorage() as group_storage:
                    entity_data = group_storage.get_group_preview(invitation_id)
                    if not entity_data:
                        await update.message.reply_text(get_group_not_found_message())
                        return ConversationHandler.END
                    message = format_group_invitation_message(telegram_user.first_name, entity_data)

            await update.message.reply_text(
                message,
                reply_markup=get_consent_keyboard()
            )
        except Exception as e:
            logger.error(f"Error showing invitation: {e}", exc_info=True)
            # Fallback to regular onboarding
            await update.message.reply_text(
                get_welcome_message(telegram_user.first_name),
                reply_markup=get_consent_keyboard()
            )
    else:
        # Regular onboarding without invitation
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

    # User accepted consent - show photo visibility selection
    logger.info(f"User {query.from_user.id} accepted consent")

    # Track consent step
    with UserStorage() as user_storage:
        user = user_storage.get_user_by_telegram_id(query.from_user.id)
        if user:
            track_onboarding_step(user.id, "consent", 1)

    await query.edit_message_text(
        get_photo_visibility_message(),
        reply_markup=get_photo_visibility_keyboard()
    )

    return ASKING_PHOTO_VISIBILITY


async def handle_photo_visibility(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle photo visibility selection.

    Callback data: "photo_show" or "photo_hide"
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    telegram_user = query.from_user

    # Determine show_photo value
    show_photo = callback_data == "photo_show"

    logger.info(f"User {telegram_user.id} set show_photo={show_photo}")

    # Save to database and track
    with UserStorage() as user_storage:
        user = user_storage.get_user_by_telegram_id(telegram_user.id)
        if user:
            user_storage.update_profile(user.id, show_photo=show_photo)
            track_onboarding_step(user.id, "photo_visibility", 2)

    # Initialize selected sports in context and move to sports selection
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
                track_onboarding_step(user.id, "sports", 3)

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
        # User is a participant - ask about Strava
        logger.info(f"User {telegram_user.id} selected role: participant")

        # Track role selection step
        with UserStorage() as user_storage:
            user = user_storage.get_user_by_telegram_id(telegram_user.id)
            if user:
                track_onboarding_step(user.id, "role", 4)

        keyboard = [
            [InlineKeyboardButton("Да, добавить ссылку", callback_data="strava_yes")],
            [InlineKeyboardButton("Пропустить →", callback_data="strava_skip")]
        ]

        await query.edit_message_text(
            "🏃 У тебя есть профиль на Strava?\n\n"
            "Если хочешь, можешь добавить ссылку на свой профиль — "
            "другие участники смогут найти тебя там.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return ASKING_STRAVA

    # Note: role_organizer is handled by organizer_conv_handler
    # This handler only processes role_participant

    return SELECTING_ROLE


async def handle_strava_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle Strava link question responses (yes/skip/skip_input).

    - strava_yes: Ask user to send Strava link
    - strava_skip: Skip to intro message (initial choice)
    - strava_skip_input: Skip after trying to input link
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    telegram_user = query.from_user

    if callback_data in ("strava_skip", "strava_skip_input"):
        # Skip Strava link - proceed to intro
        logger.info(f"User {telegram_user.id} skipped Strava link")

        await query.edit_message_text(
            get_intro_message(),
            reply_markup=get_intro_done_keyboard()
        )

        return SHOWING_INTRO

    elif callback_data == "strava_yes":
        # User wants to add Strava link - ask for it
        logger.info(f"User {telegram_user.id} wants to add Strava link")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭ Пропустить", callback_data="strava_skip_input")]
        ])

        await query.edit_message_text(
            "Отправь ссылку на свой профиль Strava\n\n"
            "Например: https://www.strava.com/athletes/12345\n\n"
            "💡 Можешь скопировать ссылку из профиля в приложении Strava.",
            reply_markup=keyboard
        )

        return ASKING_STRAVA

    return ASKING_STRAVA


async def handle_strava_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle Strava link text input.

    Validate, check uniqueness, and save Strava link to user profile, then proceed to intro.
    """
    from bot.validators import validate_strava_link

    message = update.message
    telegram_user = message.from_user
    strava_link = message.text.strip()

    logger.info(f"User {telegram_user.id} sent Strava link: {strava_link}")

    # Validate Strava link format
    is_valid, result = validate_strava_link(strava_link)

    if not is_valid:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⏭ Пропустить", callback_data="strava_skip_input")]
        ])
        await message.reply_text(f"❌ {result}", reply_markup=keyboard)
        return ASKING_STRAVA

    # Check uniqueness
    with UserStorage() as user_storage:
        user = user_storage.get_user_by_telegram_id(telegram_user.id)
        if user:
            # Check if this Strava link is already used by another user
            if not user_storage.is_strava_link_unique(result, exclude_user_id=user.id):
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("⏭ Пропустить", callback_data="strava_skip_input")]
                ])
                await message.reply_text(
                    "❌ Эта ссылка Strava уже используется другим пользователем.\n\n"
                    "Попробуй указать другую ссылку или пропусти этот шаг.",
                    reply_markup=keyboard
                )
                return ASKING_STRAVA

            # Save the link
            user_storage.update_profile(user.id, strava_link=result)
            logger.info(f"Saved Strava link for user {user.id}")

    # Confirmation message
    await message.reply_text("✅ Ссылка сохранена!")

    # Show intro message
    await message.reply_text(
        get_intro_message(),
        reply_markup=get_intro_done_keyboard()
    )

    return SHOWING_INTRO


async def complete_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Complete onboarding flow.

    Mark user as onboarded and show completion message with WebApp button.
    If user came via invitation - automatically add to club/group.
    """
    query = update.callback_query
    await query.answer()

    telegram_user = query.from_user
    invitation_type = context.user_data.get('invitation_type')
    invitation_id = context.user_data.get('invitation_id')

    # Mark onboarding as complete
    with UserStorage() as user_storage:
        user = user_storage.get_user_by_telegram_id(telegram_user.id)
        if not user:
            await query.edit_message_text("Произошла ошибка")
            return ConversationHandler.END

        user_storage.mark_onboarding_complete(user.id)
        logger.info(f"User {telegram_user.id} completed onboarding")

        # Track onboarding completion
        track_onboarding_step(user.id, "intro", 5)
        track_onboarding_complete(user.id)

        # If has invitation - automatically add to club/group
        if invitation_type and invitation_id:
            try:
                with MembershipStorage() as membership_storage:
                    if invitation_type == "club":
                        membership_storage.add_member_to_club(user.id, invitation_id)
                        logger.info(f"Auto-joined user {user.id} to club {invitation_id}")

                        with ClubStorage() as club_storage:
                            entity_data = club_storage.get_club_preview(invitation_id)
                            entity_name = entity_data['name'] if entity_data else "клуб"
                            webapp_url = f"{settings.app_url}?startapp=club_{invitation_id}"
                    else:  # group
                        membership_storage.add_member_to_group(user.id, invitation_id)
                        logger.info(f"Auto-joined user {user.id} to group {invitation_id}")

                        with GroupStorage() as group_storage:
                            entity_data = group_storage.get_group_preview(invitation_id)
                            entity_name = entity_data['name'] if entity_data else "группу"
                            webapp_url = f"{settings.app_url}?startapp=group_{invitation_id}"

                # Success message for invitation
                await query.edit_message_text(
                    get_join_success_message(entity_name, "клуба" if invitation_type == "club" else "группы")
                )

                await query.message.reply_text(
                    "Открой приложение:",
                    reply_markup=get_webapp_button(webapp_url, f"🚀 Открыть {entity_name}")
                )

            except Exception as e:
                logger.error(f"Error auto-joining after onboarding: {e}", exc_info=True)
                # Fallback to regular completion
                await query.edit_message_text(
                    get_completion_message(user.first_name, user.username)
                )
                await query.message.reply_text(
                    "Открой приложение:",
                    reply_markup=get_webapp_button(settings.app_url)
                )
        else:
            # Regular completion without invitation
            await query.edit_message_text(
                get_completion_message(user.first_name, user.username)
            )

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
        ASKING_PHOTO_VISIBILITY: [
            CallbackQueryHandler(handle_photo_visibility, pattern="^photo_")
        ],
        SELECTING_SPORTS: [
            CallbackQueryHandler(handle_sports_selection, pattern="^sport_")
        ],
        SELECTING_ROLE: [
            CallbackQueryHandler(handle_role_selection, pattern="^role_participant$")
        ],
        ASKING_STRAVA: [
            CallbackQueryHandler(handle_strava_response, pattern="^strava_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_strava_link)
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
