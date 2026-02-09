"""
Strava Bot Handler

Commands:
- /connect_strava - Show button to connect Strava account
- /disconnect_strava - Disconnect Strava account

Callback handlers:
- strava_* - OAuth connect/disconnect flow
- sc_{id} - Confirm Strava match (high confidence)
- si_{id} - Check-in via Strava match (medium confidence)
- sr_{id} - Reject Strava match
"""
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from config import settings
from storage.db import (
    SessionLocal, User, Participation, PendingStravaMatch,
    ParticipationStatus, PostTrainingNotification, PostTrainingNotificationStatus
)

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


async def handle_strava_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle Strava match confirmation (high confidence).

    Saves Strava link to existing participation.
    Callback data: sc_{match_id}
    """
    query = update.callback_query
    await query.answer()

    match_id = query.data.replace("sc_", "")

    session = SessionLocal()
    try:
        match = session.query(PendingStravaMatch).filter(
            PendingStravaMatch.id == match_id
        ).first()

        if not match:
            await query.edit_message_text("❌ Подтверждение истекло или уже обработано")
            return

        # Extract data before deleting (double-click protection)
        match_activity_id = match.activity_id
        match_user_id = match.user_id
        match_strava_activity_id = match.strava_activity_id
        match_strava_activity_data = match.strava_activity_data

        # Get activity title before deleting
        activity = match.activity
        activity_title = activity.title if activity else "Тренировка"

        # Delete match immediately to prevent double-click
        session.delete(match)
        session.flush()

        # Find participation and save link
        participation = session.query(Participation).filter(
            Participation.activity_id == match_activity_id,
            Participation.user_id == match_user_id
        ).first()

        if not participation:
            await query.edit_message_text("❌ Запись на тренировку не найдена")
            session.commit()
            return

        # Save Strava data
        strava_link = f"https://strava.com/activities/{match_strava_activity_id}"
        participation.training_link = strava_link
        participation.training_link_source = "strava_auto"
        participation.strava_activity_id = match_strava_activity_id
        participation.strava_activity_data = match_strava_activity_data
        participation.status = ParticipationStatus.ATTENDED
        participation.attended = True

        # Close PostTrainingNotification if exists (prevent reminder for already-linked)
        _close_post_training_notification(session, match_activity_id, match_user_id)

        session.commit()

        # Parse distance from cached data
        strava_data = json.loads(match_strava_activity_data) if match_strava_activity_data else {}
        distance_km = strava_data.get("distance", 0) / 1000

        await query.edit_message_text(
            f"✅ Ссылка сохранена!\n\n"
            f"«{activity_title}» — {distance_km:.1f} км\n"
            f"[Открыть в Strava]({strava_link})",
            parse_mode="Markdown"
        )

        # Notify trainer
        await _notify_trainer_about_link(context.bot, session, match_activity_id, match_user_id, strava_link)

        logger.info(f"Strava match confirmed: activity={match_activity_id}, user={match_user_id}")

    except Exception as e:
        logger.error(f"Error handling strava confirm: {e}", exc_info=True)
        try:
            await query.edit_message_text("❌ Произошла ошибка")
        except Exception:
            pass
    finally:
        session.close()


async def handle_strava_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle Strava check-in (medium confidence — user was not registered).

    Creates new participation and saves Strava link.
    Callback data: si_{match_id}
    """
    query = update.callback_query
    await query.answer()

    match_id = query.data.replace("si_", "")

    session = SessionLocal()
    try:
        match = session.query(PendingStravaMatch).filter(
            PendingStravaMatch.id == match_id
        ).first()

        if not match:
            await query.edit_message_text("❌ Подтверждение истекло или уже обработано")
            return

        # Extract data before deleting (double-click protection)
        match_activity_id = match.activity_id
        match_user_id = match.user_id
        match_strava_activity_id = match.strava_activity_id
        match_strava_activity_data = match.strava_activity_data

        # Get activity title before deleting
        activity_title = match.activity.title if match.activity else "Тренировка"

        # Delete match immediately to prevent double-click
        session.delete(match)
        session.flush()

        strava_link = f"https://strava.com/activities/{match_strava_activity_id}"

        # Check if participation already exists
        existing = session.query(Participation).filter(
            Participation.activity_id == match_activity_id,
            Participation.user_id == match_user_id
        ).first()

        if existing:
            # Update existing
            existing.training_link = strava_link
            existing.training_link_source = "strava_auto"
            existing.strava_activity_id = match_strava_activity_id
            existing.strava_activity_data = match_strava_activity_data
            existing.status = ParticipationStatus.ATTENDED
            existing.attended = True
        else:
            # Create new participation
            participation = Participation(
                activity_id=match_activity_id,
                user_id=match_user_id,
                status=ParticipationStatus.ATTENDED,
                attended=True,
                training_link=strava_link,
                training_link_source="strava_auto",
                strava_activity_id=match_strava_activity_id,
                strava_activity_data=match_strava_activity_data
            )
            session.add(participation)

        # Close PostTrainingNotification if exists (prevent reminder for already-linked)
        _close_post_training_notification(session, match_activity_id, match_user_id)

        session.commit()

        strava_data = json.loads(match_strava_activity_data) if match_strava_activity_data else {}
        distance_km = strava_data.get("distance", 0) / 1000

        await query.edit_message_text(
            f"✅ Отмечено и ссылка сохранена!\n\n"
            f"«{activity_title}» — {distance_km:.1f} км\n"
            f"[Открыть в Strava]({strava_link})",
            parse_mode="Markdown"
        )

        # Notify trainer
        await _notify_trainer_about_link(context.bot, session, match_activity_id, match_user_id, strava_link)

        logger.info(f"Strava checkin: activity={match_activity_id}, user={match_user_id}")

    except Exception as e:
        logger.error(f"Error handling strava checkin: {e}", exc_info=True)
        try:
            await query.edit_message_text("❌ Произошла ошибка")
        except Exception:
            pass
    finally:
        session.close()


async def handle_strava_reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle Strava match rejection.

    Callback data: sr_{match_id}
    """
    query = update.callback_query
    await query.answer()

    match_id = query.data.replace("sr_", "")

    session = SessionLocal()
    try:
        match = session.query(PendingStravaMatch).filter(
            PendingStravaMatch.id == match_id
        ).first()

        if not match:
            await query.edit_message_text("❌ Подтверждение истекло или уже обработано")
            return

        user_id = match.user_id
        session.delete(match)
        session.commit()

        await query.edit_message_text("👌 Ок, пропускаем эту тренировку")

        logger.info(f"Strava match rejected: user={user_id}")

    except Exception as e:
        logger.error(f"Error handling strava reject: {e}", exc_info=True)
        try:
            await query.edit_message_text("❌ Произошла ошибка")
        except Exception:
            pass
    finally:
        session.close()


def _close_post_training_notification(session, activity_id, user_id):
    """Mark PostTrainingNotification as LINK_SUBMITTED when Strava auto-links."""
    from datetime import datetime
    notification = session.query(PostTrainingNotification).filter(
        PostTrainingNotification.activity_id == activity_id,
        PostTrainingNotification.user_id == user_id,
        PostTrainingNotification.status.in_([
            PostTrainingNotificationStatus.SENT,
            PostTrainingNotificationStatus.REMINDER_SENT
        ])
    ).first()
    if notification:
        notification.status = PostTrainingNotificationStatus.LINK_SUBMITTED
        notification.responded_at = datetime.utcnow()
        logger.info(f"Closed post-training notification for user {user_id}, activity {activity_id}")


async def _notify_trainer_about_link(bot, session, activity_id, user_id, link):
    """Notify trainer that a participant submitted a Strava link."""
    try:
        from bot.post_training_handler import get_activity_trainer_info, get_user_name
        from bot.activity_notifications import send_trainer_link_notification

        trainer_telegram_id, activity_title = get_activity_trainer_info(activity_id)
        if trainer_telegram_id:
            participant_name = get_user_name(user_id)
            await send_trainer_link_notification(
                bot=bot,
                trainer_telegram_id=trainer_telegram_id,
                participant_name=participant_name,
                activity_title=activity_title,
                training_link=link
            )
    except Exception as e:
        logger.error(f"Failed to notify trainer about Strava link: {e}")


def get_strava_handlers():
    """
    Get Strava command and callback handlers.

    Returns:
        List of handlers to be added to the bot application
    """
    return [
        CommandHandler("connect_strava", connect_strava_command),
        CommandHandler("disconnect_strava", disconnect_strava_command),
        # Strava match confirmation callbacks (must be before generic strava_ pattern)
        CallbackQueryHandler(handle_strava_confirm, pattern=r"^sc_"),
        CallbackQueryHandler(handle_strava_checkin, pattern=r"^si_"),
        CallbackQueryHandler(handle_strava_reject, pattern=r"^sr_"),
        # Generic strava OAuth callbacks
        CallbackQueryHandler(handle_strava_callback, pattern=r"^strava_"),
    ]
