"""
Organizer Handler for Telegram Bot

Implements Flow 3: Organizer - Club Creation Request
Handles multi-step form for club creation with manual moderation.
"""

import logging
import json
from telegram import Update
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
from config import settings
from bot.keyboards import (
    get_org_type_keyboard,
    get_club_form_start_keyboard,
    get_sports_selection_keyboard,
    get_telegram_group_keyboard,
    get_contact_method_keyboard,
    get_club_access_keyboard,
    get_club_request_summary_keyboard,
    get_webapp_button
)
from bot.messages import (
    get_org_welcome_message,
    get_club_creation_info_message,
    get_club_name_prompt,
    get_club_description_prompt,
    get_club_sports_prompt,
    get_club_members_count_prompt,
    get_club_groups_count_prompt,
    get_club_telegram_group_prompt,
    get_club_telegram_instructions,
    get_club_contact_prompt,
    get_club_access_prompt,
    get_club_request_summary,
    get_club_request_success_message,
    get_group_creation_redirect_message
)
from bot.validators import (
    validate_club_name,
    validate_description,
    validate_members_count,
    validate_groups_count,
    validate_telegram_link,
    validate_phone_number
)

logger = logging.getLogger(__name__)

# Conversation states for organizer flow
ORG_CHOICE = 10           # Choose between club or group
CLUB_NAME = 11            # Enter club name
CLUB_DESCRIPTION = 12     # Enter club description
CLUB_SPORTS = 13          # Select sports (multi-select)
CLUB_MEMBERS_COUNT = 14   # Enter members count
CLUB_GROUPS_COUNT = 15    # Enter groups count
CLUB_TELEGRAM = 16        # Enter telegram group link (optional)
CLUB_CONTACT = 17         # Enter contact info
CLUB_ACCESS = 19          # Select club access type (open/closed)
CLUB_CONFIRM = 18         # Confirm and submit


async def start_organizer_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point for organizer flow.

    Shows welcome message and asks: Club or Group?
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user

    # Get or create user in DB
    with UserStorage() as user_storage:
        db_user = user_storage.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        context.user_data['user_id'] = db_user.id

    # Initialize form data
    context.user_data['club_request'] = {}

    # Show welcome and choice
    message = get_org_welcome_message()
    await query.edit_message_text(
        message,
        reply_markup=get_org_type_keyboard()
    )

    return ORG_CHOICE


async def handle_org_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle choice between Club or Group.
    """
    query = update.callback_query
    await query.answer()

    choice = query.data  # org_club or org_group

    if choice == "org_club":
        # Show club creation info
        message = get_club_creation_info_message()
        await query.edit_message_text(
            message,
            reply_markup=get_club_form_start_keyboard()
        )
        return ORG_CHOICE  # Stay in same state, wait for form_start or back

    elif choice == "org_group":
        # Redirect to app for group creation
        message = get_group_creation_redirect_message()
        webapp_url = settings.app_url
        await query.edit_message_text(message)
        await query.message.reply_text(
            "Открой приложение:",
            reply_markup=get_webapp_button(webapp_url, "🚀 Открыть Ayda Run")
        )
        return ConversationHandler.END

    elif choice == "org_back":
        # Go back to role selection (if came from onboarding)
        # For now, just end conversation
        await query.edit_message_text(
            "Хорошо! Если передумаешь — напиши /start"
        )
        return ConversationHandler.END

    elif choice == "form_start":
        # Start collecting club data
        message = get_club_name_prompt()
        await query.edit_message_text(message)
        return CLUB_NAME

    elif choice == "form_back":
        # Go back to org choice
        message = get_org_welcome_message()
        await query.edit_message_text(
            message,
            reply_markup=get_org_type_keyboard()
        )
        return ORG_CHOICE


async def handle_club_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle club name input.
    """
    text = update.message.text

    # Validate
    is_valid, result = validate_club_name(text)

    if not is_valid:
        await update.message.reply_text(
            f"❌ {result}\n\nПопробуй ещё раз:"
        )
        return CLUB_NAME

    # Save club name
    context.user_data['club_request']['name'] = result

    # Ask for description
    message = get_club_description_prompt(result)
    await update.message.reply_text(message)

    return CLUB_DESCRIPTION


async def handle_club_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle club description input.
    """
    text = update.message.text

    # Validate
    is_valid, result = validate_description(text)

    if not is_valid:
        await update.message.reply_text(
            f"❌ {result}\n\nПопробуй ещё раз:"
        )
        return CLUB_DESCRIPTION

    # Save description
    context.user_data['club_request']['description'] = result

    # Initialize selected sports
    context.user_data['club_request']['sports'] = []

    # Ask for sports
    message = get_club_sports_prompt()
    await update.message.reply_text(
        message,
        reply_markup=get_sports_selection_keyboard([])
    )

    return CLUB_SPORTS


async def handle_club_sports_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle sports selection (multi-select).
    """
    query = update.callback_query
    await query.answer()

    selected_sports = context.user_data['club_request'].get('sports', [])

    if query.data == "sport_done":
        if not selected_sports:
            await query.answer("⚠️ Выбери хотя бы один вид спорта", show_alert=True)
            return CLUB_SPORTS

        # Save sports and move to next step
        context.user_data['club_request']['sports'] = selected_sports

        # Ask for members count
        message = get_club_members_count_prompt()
        await query.edit_message_text(message)
        return CLUB_MEMBERS_COUNT

    elif query.data == "sport_skip":
        # Allow skipping
        context.user_data['club_request']['sports'] = []
        message = get_club_members_count_prompt()
        await query.edit_message_text(message)
        return CLUB_MEMBERS_COUNT

    elif query.data.startswith("sport_toggle_"):
        # Toggle sport selection
        sport_id = query.data.replace("sport_toggle_", "")

        if sport_id in selected_sports:
            selected_sports.remove(sport_id)
        else:
            selected_sports.append(sport_id)

        context.user_data['club_request']['sports'] = selected_sports

        # Update keyboard
        await query.edit_message_reply_markup(
            reply_markup=get_sports_selection_keyboard(selected_sports)
        )

        return CLUB_SPORTS


async def handle_club_members_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle members count input.
    """
    text = update.message.text

    # Validate
    is_valid, result = validate_members_count(text)

    if not is_valid:
        await update.message.reply_text(
            f"❌ {result}\n\nПопробуй ещё раз:"
        )
        return CLUB_MEMBERS_COUNT

    # Save members count
    context.user_data['club_request']['members_count'] = result

    # Ask for groups count
    message = get_club_groups_count_prompt()
    await update.message.reply_text(message)

    return CLUB_GROUPS_COUNT


async def handle_club_groups_count(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle groups count input.
    """
    text = update.message.text

    # Validate
    is_valid, result = validate_groups_count(text)

    if not is_valid:
        await update.message.reply_text(
            f"❌ {result}\n\nПопробуй ещё раз:"
        )
        return CLUB_GROUPS_COUNT

    # Save groups count
    context.user_data['club_request']['groups_count'] = result

    # Ask about Telegram group
    message = get_club_telegram_group_prompt()
    await update.message.reply_text(
        message,
        reply_markup=get_telegram_group_keyboard()
    )

    return CLUB_TELEGRAM


async def handle_club_telegram_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle Telegram group connection choice.
    """
    query = update.callback_query
    await query.answer()

    choice = query.data  # telegram_connect or telegram_skip

    if choice == "telegram_connect":
        # Show instructions
        message = get_club_telegram_instructions()
        await query.edit_message_text(message)
        return CLUB_TELEGRAM  # Wait for link input

    elif choice == "telegram_skip":
        # Skip telegram group
        context.user_data['club_request']['telegram_group_link'] = None

        # Ask for contact
        user = update.effective_user
        message = get_club_contact_prompt(user.username)
        await query.edit_message_text(
            message,
            reply_markup=get_contact_method_keyboard()
        )
        return CLUB_CONTACT


async def handle_club_telegram_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle Telegram group link input.
    """
    text = update.message.text

    # Validate
    is_valid, result = validate_telegram_link(text)

    if not is_valid:
        await update.message.reply_text(
            f"❌ {result}\n\nПопробуй ещё раз или введи /skip чтобы пропустить:"
        )
        return CLUB_TELEGRAM

    # Save telegram link
    context.user_data['club_request']['telegram_group_link'] = result

    # Ask for contact
    user = update.effective_user
    message = get_club_contact_prompt(user.username)
    await update.message.reply_text(
        message,
        reply_markup=get_contact_method_keyboard()
    )

    return CLUB_CONTACT


async def handle_club_contact_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle contact method choice.
    """
    query = update.callback_query
    await query.answer()

    choice = query.data  # contact_telegram or contact_phone

    user = update.effective_user

    if choice == "contact_telegram":
        # Use Telegram username
        contact = f"@{user.username}" if user.username else f"Telegram ID: {user.id}"
        context.user_data['club_request']['contact'] = contact

        # Show access type selection
        await query.edit_message_text(
            get_club_access_prompt(),
            reply_markup=get_club_access_keyboard()
        )
        return CLUB_ACCESS

    elif choice == "contact_phone":
        # Ask for phone number
        await query.edit_message_text(
            "📱 Напиши свой номер телефона или WhatsApp:\n\n"
            "Формат: +7XXXXXXXXXX"
        )
        return CLUB_CONTACT  # Wait for phone input


async def handle_club_contact_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle phone number input for contact.
    """
    text = update.message.text

    # Validate
    is_valid, result = validate_phone_number(text)

    if not is_valid:
        await update.message.reply_text(
            f"❌ {result}\n\nПопробуй ещё раз:"
        )
        return CLUB_CONTACT

    # Save contact
    context.user_data['club_request']['contact'] = result

    # Show access type selection
    await update.message.reply_text(
        get_club_access_prompt(),
        reply_markup=get_club_access_keyboard()
    )

    return CLUB_ACCESS


async def handle_club_access_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle club access type choice (open/closed).
    """
    query = update.callback_query
    await query.answer()

    choice = query.data  # access_open or access_closed

    # Determine is_open value
    is_open = choice == "access_open"
    context.user_data['club_request']['is_open'] = is_open

    logger.info(f"User {query.from_user.id} set club is_open={is_open}")

    # Show summary
    await show_club_request_summary(query, context)
    return CLUB_CONFIRM


async def show_club_request_summary(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show club request summary for confirmation.
    """
    message = get_club_request_summary(context.user_data['club_request'])
    await query.edit_message_text(
        message,
        reply_markup=get_club_request_summary_keyboard()
    )


async def handle_club_request_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle final confirmation and submission of club request.
    """
    query = update.callback_query
    await query.answer()

    choice = query.data

    if choice == "request_submit":
        # Save club request to database
        request_data = context.user_data['club_request']
        request_data['user_id'] = context.user_data['user_id']

        with ClubStorage() as club_storage:
            club_request = club_storage.create_club_request(request_data)

            if not club_request:
                await query.edit_message_text(
                    "❌ Ошибка при сохранении заявки.\n\n"
                    "Попробуй ещё раз позже или обратись в поддержку."
                )
                return ConversationHandler.END

            # Send notification to admin
            from bot.admin_notifications import send_club_request_notification
            await send_club_request_notification(
                context.bot,
                club_request.id,
                request_data
            )

            # Show success message
            message = get_club_request_success_message()
            webapp_url = settings.app_url

            await query.edit_message_text(message)
            await query.message.reply_text(
                "А пока можешь посмотреть как работает приложение:",
                reply_markup=get_webapp_button(webapp_url, "🚀 Открыть Ayda Run")
            )

            logger.info(f"Club request created: {club_request.id} by user {context.user_data['user_id']}")

            return ConversationHandler.END


async def handle_skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle /skip command during telegram link input.
    """
    # Skip telegram group
    context.user_data['club_request']['telegram_group_link'] = None

    # Ask for contact
    user = update.effective_user
    message = get_club_contact_prompt(user.username)
    await update.message.reply_text(
        message,
        reply_markup=get_contact_method_keyboard()
    )

    return CLUB_CONTACT


async def cancel_organizer_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel organizer flow.
    """
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "Создание клуба отменено.\n\n"
            "Если передумаешь — напиши /start"
        )
    else:
        await update.message.reply_text(
            "Создание клуба отменено.\n\n"
            "Если передумаешь — напиши /start"
        )

    # Clear user data
    context.user_data.clear()

    return ConversationHandler.END


# Organizer ConversationHandler
organizer_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_organizer_flow, pattern="^role_organizer$")
    ],
    states={
        ORG_CHOICE: [
            CallbackQueryHandler(handle_org_choice, pattern="^(org_club|org_group|org_back|form_start|form_back)$")
        ],
        CLUB_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_club_name)
        ],
        CLUB_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_club_description)
        ],
        CLUB_SPORTS: [
            CallbackQueryHandler(handle_club_sports_selection, pattern="^sport_")
        ],
        CLUB_MEMBERS_COUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_club_members_count)
        ],
        CLUB_GROUPS_COUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_club_groups_count)
        ],
        CLUB_TELEGRAM: [
            CallbackQueryHandler(handle_club_telegram_choice, pattern="^telegram_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_club_telegram_link),
            CommandHandler("skip", handle_skip_command)
        ],
        CLUB_CONTACT: [
            CallbackQueryHandler(handle_club_contact_choice, pattern="^contact_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_club_contact_phone)
        ],
        CLUB_ACCESS: [
            CallbackQueryHandler(handle_club_access_choice, pattern="^access_")
        ],
        CLUB_CONFIRM: [
            CallbackQueryHandler(handle_club_request_confirm, pattern="^request_")
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_organizer_flow),
        CallbackQueryHandler(cancel_organizer_flow, pattern="^cancel$")
    ],
    conversation_timeout=600,  # 10 minutes for longer form
)
