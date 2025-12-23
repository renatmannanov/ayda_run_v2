"""
Confirmation Handler

Handles callback queries for attendance confirmation buttons.
When user clicks "Участвовал" or "Пропустил" after activity.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from storage.db import SessionLocal, Participation, Activity, User, ParticipationStatus

logger = logging.getLogger(__name__)


async def handle_confirmation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle attendance confirmation callback.

    Callback data format: confirm_attended_{activity_id} or confirm_missed_{activity_id}

    Args:
        update: Telegram Update object
        context: Callback context
    """
    query = update.callback_query
    await query.answer()

    # Parse callback data
    data = query.data
    if not data.startswith("confirm_"):
        return

    parts = data.split("_", 2)  # ["confirm", "attended/missed", "activity_id"]
    if len(parts) != 3:
        logger.error(f"Invalid confirmation callback data: {data}")
        await query.edit_message_text("❌ Ошибка: неверный формат данных")
        return

    action = parts[1]  # "attended" or "missed"
    activity_id = parts[2]

    if action not in ["attended", "missed"]:
        logger.error(f"Invalid confirmation action: {action}")
        await query.edit_message_text("❌ Ошибка: неверное действие")
        return

    # Get user from Telegram
    telegram_user = update.effective_user
    if not telegram_user:
        await query.edit_message_text("❌ Ошибка: не удалось определить пользователя")
        return

    session = SessionLocal()
    try:
        # Find user in database
        user = session.query(User).filter(User.telegram_id == telegram_user.id).first()
        if not user:
            await query.edit_message_text("❌ Ошибка: пользователь не найден")
            return

        # Find participation
        participation = session.query(Participation).filter(
            Participation.activity_id == activity_id,
            Participation.user_id == user.id
        ).first()

        if not participation:
            await query.edit_message_text("❌ Ошибка: вы не были записаны на эту активность")
            return

        # Check if already confirmed
        if participation.status in [ParticipationStatus.ATTENDED, ParticipationStatus.MISSED]:
            status_text = "участвовал" if participation.status == ParticipationStatus.ATTENDED else "пропустил"
            await query.edit_message_text(f"ℹ️ Вы уже отметили, что {status_text}")
            return

        # Check if participation is in awaiting status
        if participation.status != ParticipationStatus.AWAITING:
            await query.edit_message_text(
                f"❌ Нельзя подтвердить участие. Текущий статус: {participation.status.value}"
            )
            return

        # Get activity for title
        activity = session.query(Activity).filter(Activity.id == activity_id).first()
        activity_title = activity.title if activity else "Активность"

        # Update participation status
        if action == "attended":
            participation.status = ParticipationStatus.ATTENDED
            participation.attended = True
            response_text = f"✅ Отмечено: Участвовал\n\n\"{activity_title}\"\n\nОтлично! Так держать! 💪"
        else:
            participation.status = ParticipationStatus.MISSED
            participation.attended = False
            response_text = f"📝 Отмечено: Пропустил\n\n\"{activity_title}\"\n\nВ следующий раз обязательно получится!"

        session.commit()

        # Update message (remove buttons)
        await query.edit_message_text(response_text)

        logger.info(f"User {user.id} confirmed {action} for activity {activity_id}")

    except Exception as e:
        logger.error(f"Error handling confirmation callback: {e}", exc_info=True)
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")
        session.rollback()

    finally:
        session.close()


def get_confirmation_handler() -> CallbackQueryHandler:
    """
    Get CallbackQueryHandler for confirmation callbacks.

    Returns:
        CallbackQueryHandler configured for confirm_* pattern
    """
    return CallbackQueryHandler(
        handle_confirmation_callback,
        pattern=r"^confirm_(attended|missed)_"
    )
