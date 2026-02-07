"""
Strava Bot Handler

Commands:
- /connect_strava - Show button to connect Strava account
- /disconnect_strava - Disconnect Strava account

Also handles strava-related callback queries.
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from config import settings
from storage.db import SessionLocal, User

logger = logging.getLogger(__name__)


async def connect_strava_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /connect_strava command.

    Shows button to start OAuth flow if not connected,
    or status message if already connected.
    """
    telegram_user = update.effective_user
    if not telegram_user:
        return

    # Only work in private chat
    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "Эта команда работает только в личных сообщениях с ботом."
        )
        return

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_user.id).first()
        if not user:
            await update.message.reply_text(
                "Сначала зарегистрируйся с помощью команды /start"
            )
            return

        if user.strava_athlete_id:
            keyboard = [[
                InlineKeyboardButton(
                    "Отключить Strava",
                    callback_data="strava_disconnect_confirm"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "✅ *Strava подключена*\n\n"
                "Твои тренировки будут автоматически привязываться к активностям Ayda Run.\n\n"
                f"Athlete ID: `{user.strava_athlete_id}`",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return

        # Build auth URL with user_id
        base_url = (settings.base_url or "").rstrip("/")
        if not base_url:
            await update.message.reply_text(
                "Ошибка конфигурации. Обратитесь к администратору."
            )
            return

        auth_url = f"{base_url}/api/strava/auth?user_id={user.id}"

        keyboard = [[
            InlineKeyboardButton("🏃 Подключить Strava", url=auth_url)
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🏃 *Подключи Strava*\n\n"
            "После подключения твои тренировки будут автоматически "
            "привязываться к активностям в Ayda Run.\n\n"
            "Это позволит:\n"
            "• Автоматически отмечать посещение тренировок\n"
            "• Прикреплять ссылки на Strava активности\n"
            "• Видеть статистику твоих тренировок\n\n"
            "Нажми кнопку ниже:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    finally:
        session.close()


async def disconnect_strava_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /disconnect_strava command.

    Shows confirmation before disconnecting.
    """
    telegram_user = update.effective_user
    if not telegram_user:
        return

    if update.effective_chat.type != "private":
        await update.message.reply_text(
            "Эта команда работает только в личных сообщениях с ботом."
        )
        return

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_user.id).first()
        if not user:
            await update.message.reply_text("Пользователь не найден")
            return

        if not user.strava_athlete_id:
            keyboard = [[
                InlineKeyboardButton(
                    "Подключить Strava",
                    callback_data="strava_connect"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                "ℹ️ Strava не подключена\n\n"
                "Хочешь подключить?",
                reply_markup=reply_markup
            )
            return

        keyboard = [
            [
                InlineKeyboardButton("Да, отключить", callback_data="strava_disconnect_yes"),
                InlineKeyboardButton("Отмена", callback_data="strava_disconnect_no")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚠️ *Отключить Strava?*\n\n"
            "Автоматическая привязка тренировок перестанет работать.",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    finally:
        session.close()


async def handle_strava_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle strava-related callback queries.
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    telegram_user = update.effective_user

    if not telegram_user:
        return

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.telegram_id == telegram_user.id).first()
        if not user:
            await query.edit_message_text("Пользователь не найден")
            return

        if data == "strava_connect":
            # Show connect button
            base_url = (settings.base_url or "").rstrip("/")
            if not base_url:
                await query.edit_message_text("Ошибка конфигурации")
                return

            auth_url = f"{base_url}/api/strava/auth?user_id={user.id}"
            keyboard = [[
                InlineKeyboardButton("🏃 Подключить Strava", url=auth_url)
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "🏃 *Подключи Strava*\n\n"
                "Нажми кнопку ниже для подключения:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        elif data == "strava_disconnect_confirm":
            # Show confirmation
            keyboard = [
                [
                    InlineKeyboardButton("Да, отключить", callback_data="strava_disconnect_yes"),
                    InlineKeyboardButton("Отмена", callback_data="strava_disconnect_no")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "⚠️ *Отключить Strava?*\n\n"
                "Автоматическая привязка тренировок перестанет работать.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        elif data == "strava_disconnect_yes":
            # Disconnect Strava
            if not user.strava_athlete_id:
                await query.edit_message_text("Strava уже отключена")
                return

            user.strava_athlete_id = None
            user.strava_access_token = None
            user.strava_refresh_token = None
            user.strava_token_expires_at = None
            session.commit()

            logger.info(f"User {user.id} disconnected Strava via bot")

            keyboard = [[
                InlineKeyboardButton("Подключить снова", callback_data="strava_connect")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                "✅ *Strava отключена*\n\n"
                "Автоматическая привязка тренировок больше не работает.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        elif data == "strava_disconnect_no":
            # Cancel disconnect
            await query.edit_message_text(
                "✅ Strava остается подключенной\n\n"
                "Твои тренировки продолжат автоматически привязываться к активностям."
            )

    finally:
        session.close()


def get_strava_handlers():
    """
    Get Strava command and callback handlers.

    Returns:
        List of handlers to be added to the bot application
    """
    return [
        CommandHandler("connect_strava", connect_strava_command),
        CommandHandler("disconnect_strava", disconnect_strava_command),
        CallbackQueryHandler(handle_strava_callback, pattern=r"^strava_"),
    ]
