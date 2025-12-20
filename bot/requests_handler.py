"""
Join Requests Management Commands

Provides commands for admins and users to view and manage join requests:
- /requests - View all pending requests (for admins/organizers)
- /my_requests - View user's own requests and their status
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode

from storage.db import SessionLocal, User, Club, Group, Activity, Membership, UserRole, JoinRequestStatus, JoinRequest
from storage.join_request_storage import JoinRequestStorage

logger = logging.getLogger(__name__)


async def handle_requests_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /requests command - show all pending join requests for entities where user is organizer.

    Format (2 lines per request):
    1️⃣ Иван Петров (@ivan_p) → "Almaty Runners"
       [✅ Принять] [❌ Отклонить]
    """
    telegram_user = update.message.from_user
    session = SessionLocal()

    try:
        # Get user from DB
        user = session.query(User).filter(User.telegram_id == telegram_user.id).first()

        if not user:
            await update.message.reply_text(
                "Вы не зарегистрированы в системе. Используйте /start для регистрации."
            )
            return

        # Get all clubs/groups where user is ORGANIZER or ADMIN
        memberships = session.query(Membership).filter(
            Membership.user_id == user.id,
            Membership.role.in_([UserRole.ORGANIZER, UserRole.ADMIN])
        ).all()

        # Debug: log all memberships for this user
        all_user_memberships = session.query(Membership).filter(Membership.user_id == user.id).all()
        logger.info(f"User {user.username} has {len(all_user_memberships)} total memberships")
        for m in all_user_memberships:
            logger.info(f"  - Membership role: {m.role}, club_id: {m.club_id}, group_id: {m.group_id}")

        if not memberships:
            await update.message.reply_text(
                f"У вас нет клубов или групп, где вы являетесь организатором.\n\nВсего участий: {len(all_user_memberships)}"
            )
            return

        # Collect all pending requests
        jr_storage = JoinRequestStorage(session=session)
        all_requests = []

        for membership in memberships:
            if membership.club_id:
                # Get club requests
                club = session.query(Club).filter(Club.id == membership.club_id).first()
                if club:
                    requests = jr_storage.get_pending_requests_for_entity("club", str(club.id))
                    logger.info(f"Club '{club.name}' has {len(requests)} pending requests")
                    for req in requests:
                        req_user = session.query(User).filter(User.id == req.user_id).first()
                        if req_user:
                            all_requests.append({
                                'request': req,
                                'user': req_user,
                                'entity_type': 'club',
                                'entity_name': club.name,
                                'entity_id': str(club.id)
                            })

            if membership.group_id:
                # Get group requests
                group = session.query(Group).filter(Group.id == membership.group_id).first()
                if group:
                    requests = jr_storage.get_pending_requests_for_entity("group", str(group.id))
                    logger.info(f"Group '{group.name}' has {len(requests)} pending requests")
                    for req in requests:
                        req_user = session.query(User).filter(User.id == req.user_id).first()
                        if req_user:
                            all_requests.append({
                                'request': req,
                                'user': req_user,
                                'entity_type': 'group',
                                'entity_name': group.name,
                                'entity_id': str(group.id)
                            })

        # Also get requests for activities created by this user
        user_activities = session.query(Activity).filter(Activity.creator_id == user.id).all()
        logger.info(f"User {user.username} created {len(user_activities)} activities")

        for activity in user_activities:
            requests = jr_storage.get_pending_requests_for_entity("activity", str(activity.id))
            logger.info(f"Activity '{activity.title}' has {len(requests)} pending requests")
            for req in requests:
                req_user = session.query(User).filter(User.id == req.user_id).first()
                if req_user:
                    all_requests.append({
                        'request': req,
                        'user': req_user,
                        'entity_type': 'activity',
                        'entity_name': activity.title,
                        'entity_id': str(activity.id)
                    })

        if not all_requests:
            logger.info(f"No pending requests found for user {user.username}")
            await update.message.reply_text("📋 У вас нет ожидающих заявок.")
            return

        logger.info(f"Found {len(all_requests)} pending requests total")

        # Format message with requests
        message = "📋 Ваши заявки на рассмотрение:\n\n"

        for idx, item in enumerate(all_requests[:10], 1):  # Limit to 10 requests
            req = item['request']
            req_user = item['user']
            entity_name = item['entity_name']
            entity_type = item['entity_type']

            # Build username string
            username_str = f"@{req_user.username}" if req_user.username else "нет username"
            full_name = f"{req_user.first_name or ''} {req_user.last_name or ''}".strip() or "Без имени"

            # Line 1: User info → Entity
            message += f"{idx}️⃣ {full_name} ({username_str}) → \"{entity_name}\"\n"

            # Line 2: Buttons (inline keyboard will be added per request)
            # For now, add placeholder text
            message += f"   "

            # Add inline buttons for approve/reject
            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ Принять",
                        callback_data=f"approve_join_{entity_type}_{req.id}"
                    ),
                    InlineKeyboardButton(
                        "❌ Отклонить",
                        callback_data=f"reject_join_{entity_type}_{req.id}"
                    )
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            # Send each request as separate message with buttons
            await update.message.reply_text(
                f"{idx}️⃣ {full_name} ({username_str}) → \"{entity_name}\"",
                reply_markup=reply_markup
            )

        if len(all_requests) > 10:
            await update.message.reply_text(
                f"\n... и еще {len(all_requests) - 10} заявок.\n"
                f"Всего: {len(all_requests)}"
            )

    except Exception as e:
        logger.error(f"Error in handle_requests_command: {e}")
        await update.message.reply_text(
            "Произошла ошибка при получении заявок. Попробуйте позже."
        )

    finally:
        session.close()


async def handle_my_requests_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /my_requests command - show user's own join requests and their status.

    Shows pending, approved, and rejected requests grouped by status.
    """
    telegram_user = update.message.from_user
    session = SessionLocal()

    try:
        # Get user from DB
        user = session.query(User).filter(User.telegram_id == telegram_user.id).first()

        if not user:
            await update.message.reply_text(
                "Вы не зарегистрированы в системе. Используйте /start для регистрации."
            )
            return

        # Get all user's requests across all statuses
        all_requests = session.query(JoinRequest).filter(
            JoinRequest.user_id == user.id
        ).order_by(JoinRequest.created_at.desc()).all()

        if not all_requests:
            await update.message.reply_text(
                "У вас нет заявок на вступление."
            )
            return

        # Group by status
        pending = []
        approved = []
        rejected = []
        expired = []

        for req in all_requests:
            # Get entity name
            entity_name = "Unknown"
            entity_type = ""

            if req.club_id:
                club = session.query(Club).filter(Club.id == req.club_id).first()
                entity_name = club.name if club else "Unknown Club"
                entity_type = "клуб"
            elif req.group_id:
                group = session.query(Group).filter(Group.id == req.group_id).first()
                entity_name = group.name if group else "Unknown Group"
                entity_type = "группа"
            elif req.activity_id:
                activity = session.query(Activity).filter(Activity.id == req.activity_id).first()
                entity_name = activity.title if activity else "Unknown Activity"
                entity_type = "активность"

            # Calculate time ago
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            delta = now - req.created_at.replace(tzinfo=timezone.utc)

            if delta.days > 0:
                time_ago = f"{delta.days} дн. назад"
            elif delta.seconds // 3600 > 0:
                time_ago = f"{delta.seconds // 3600} ч. назад"
            elif delta.seconds // 60 > 0:
                time_ago = f"{delta.seconds // 60} мин. назад"
            else:
                time_ago = "только что"

            request_info = {
                'name': entity_name,
                'type': entity_type,
                'time': time_ago
            }

            if req.status == JoinRequestStatus.PENDING:
                pending.append(request_info)
            elif req.status == JoinRequestStatus.APPROVED:
                approved.append(request_info)
            elif req.status == JoinRequestStatus.REJECTED:
                rejected.append(request_info)
            elif req.status == JoinRequestStatus.EXPIRED:
                expired.append(request_info)

        # Build message
        message = "📨 Ваши заявки:\n\n"

        if pending:
            message += "🟡 Ожидают рассмотрения\n"
            for req in pending:
                message += f"• \"{req['name']}\" ({req['type']}, отправлено {req['time']})\n"
            message += "\n"

        if approved:
            message += "✅ Одобрены\n"
            for req in approved[:5]:  # Show last 5
                message += f"• \"{req['name']}\" ({req['type']}, одобрено {req['time']})\n"
            if len(approved) > 5:
                message += f"... и еще {len(approved) - 5}\n"
            message += "\n"

        if rejected:
            message += "❌ Отклонены\n"
            for req in rejected[:5]:  # Show last 5
                message += f"• \"{req['name']}\" ({req['type']}, отклонено {req['time']})\n"
            if len(rejected) > 5:
                message += f"... и еще {len(rejected) - 5}\n"
            message += "\n"

        if expired:
            message += "⏱ Истекли\n"
            for req in expired[:3]:  # Show last 3
                message += f"• \"{req['name']}\" ({req['type']}, истекло {req['time']})\n"
            if len(expired) > 3:
                message += f"... и еще {len(expired) - 3}\n"

        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error in handle_my_requests_command: {e}")
        await update.message.reply_text(
            "Произошла ошибка при получении ваших заявок. Попробуйте позже."
        )

    finally:
        session.close()


def get_request_management_handlers():
    """
    Get list of command handlers for request management.

    Returns:
        List of CommandHandler objects
    """
    return [
        CommandHandler("requests", handle_requests_command),
        CommandHandler("my_requests", handle_my_requests_command)
    ]
