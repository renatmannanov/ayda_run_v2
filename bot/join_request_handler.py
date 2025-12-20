"""
Join Request Callback Handler

Handles callback queries from join request approve/reject buttons.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from storage.db import SessionLocal, User, Club, Group, Activity, Membership, Participation, UserRole, JoinRequestStatus, ParticipationStatus
from storage.join_request_storage import JoinRequestStorage
from bot.join_request_notifications import send_approval_notification, send_rejection_notification

logger = logging.getLogger(__name__)


async def handle_join_request_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries from join request buttons.

    Callback data format:
    - approve_join_{entity_type}_{request_id}
    - reject_join_{entity_type}_{request_id}

    Args:
        update: Telegram Update
        context: Callback context
    """
    query = update.callback_query
    await query.answer()

    # Parse callback data
    callback_data = query.data
    parts = callback_data.split('_')

    if len(parts) != 4:
        await query.edit_message_text("Ошибка: неверный формат данных")
        return

    action = parts[0]  # "approve" or "reject"
    entity_type = parts[2]  # "club", "group", or "activity"
    request_id = parts[3]  # UUID

    session = SessionLocal()

    try:
        # Get join request
        jr_storage = JoinRequestStorage(session=session)
        join_request = jr_storage.get_join_request(request_id)

        if not join_request:
            await query.edit_message_text("Ошибка: заявка не найдена")
            return

        # Check if already processed
        if join_request.status != JoinRequestStatus.PENDING:
            await query.edit_message_text(
                f"Эта заявка уже обработана (статус: {join_request.status.value})"
            )
            return

        # Get user
        user = session.query(User).filter(User.id == join_request.user_id).first()
        if not user:
            await query.edit_message_text("Ошибка: пользователь не найден")
            return

        # Get entity (club/group/activity)
        entity = None
        entity_name = "Unknown"

        if entity_type == "club":
            entity = session.query(Club).filter(Club.id == join_request.club_id).first()
        elif entity_type == "group":
            entity = session.query(Group).filter(Group.id == join_request.group_id).first()
        elif entity_type == "activity":
            entity = session.query(Activity).filter(Activity.id == join_request.activity_id).first()

        if not entity:
            await query.edit_message_text(f"Ошибка: {entity_type} не найден")
            return

        entity_name = entity.name if hasattr(entity, 'name') else entity.title

        # Process action
        if action == "approve":
            # Update request status
            jr_storage.update_request_status(request_id, JoinRequestStatus.APPROVED)

            if entity_type == "activity":
                # For activities - create Participation (not Membership!)
                existing_participation = session.query(Participation).filter(
                    Participation.user_id == user.id,
                    Participation.activity_id == join_request.activity_id
                ).first()

                if existing_participation:
                    await query.edit_message_text(
                        f"Пользователь {user.first_name} уже записан на {entity_name}"
                    )
                    return

                participation = Participation(
                    user_id=user.id,
                    activity_id=join_request.activity_id,
                    status=ParticipationStatus.REGISTERED
                )
                session.add(participation)
                session.commit()

            else:
                # For clubs/groups - create Membership
                entity_id = join_request.club_id or join_request.group_id

                existing_membership = session.query(Membership).filter(
                    Membership.user_id == user.id
                )

                if entity_type == "club":
                    existing_membership = existing_membership.filter(Membership.club_id == entity_id)
                elif entity_type == "group":
                    existing_membership = existing_membership.filter(Membership.group_id == entity_id)

                if existing_membership.first():
                    await query.edit_message_text(
                        f"Пользователь {user.first_name} уже является участником {entity_name}"
                    )
                    return

                # Create membership
                membership_data = {"user_id": user.id, "role": UserRole.MEMBER}

                if entity_type == "club":
                    membership_data["club_id"] = entity_id
                elif entity_type == "group":
                    membership_data["group_id"] = entity_id

                membership = Membership(**membership_data)
                session.add(membership)
                session.commit()

            # Send approval notification to user
            await send_approval_notification(
                context.bot,
                user.telegram_id,
                entity_name,
                entity_type
            )

            # Update message
            await query.edit_message_text(
                f"Заявка одобрена!\n\n"
                f"Пользователь {user.first_name} (@{user.username or 'нет username'}) "
                f"добавлен в {entity_name}"
            )

            logger.info(f"Approved join request {request_id} for user {user.id}")

        elif action == "reject":
            # Update request status
            jr_storage.update_request_status(request_id, JoinRequestStatus.REJECTED)

            # Send rejection notification to user
            await send_rejection_notification(
                context.bot,
                user.telegram_id,
                entity_name,
                entity_type
            )

            # Update message
            await query.edit_message_text(
                f"Заявка отклонена.\n\n"
                f"Пользователь {user.first_name} (@{user.username or 'нет username'}) "
                f"получил уведомление."
            )

            logger.info(f"Rejected join request {request_id} for user {user.id}")

    except Exception as e:
        logger.error(f"Error handling join request callback: {e}")
        import traceback
        traceback.print_exc()
        await query.edit_message_text(f"Ошибка при обработке заявки: {str(e)}")
        session.rollback()

    finally:
        session.close()


def get_join_request_handlers():
    """
    Get callback query handlers for join requests.

    Returns:
        List of CallbackQueryHandler instances
    """
    return [
        CallbackQueryHandler(
            handle_join_request_callback,
            pattern=r"^(approve|reject)_join_(club|group|activity)_"
        )
    ]
