"""
Sync Command Handler

Provides /sync command for organizers to check club sync status
and manually refresh Telegram member count.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.error import TelegramError

from storage.db import MembershipStatus
from storage.club_storage import ClubStorage
from storage.membership_storage import MembershipStorage

logger = logging.getLogger(__name__)


async def handle_sync_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /sync - Check and update club sync status from Telegram.
    Only for organizers/admins in group chats.
    """
    message = update.message
    if not message:
        return

    # Only works in groups
    if message.chat.type not in ["group", "supergroup"]:
        await message.reply_text(
            "ℹ️ Эта команда работает только в группах.\n\n"
            "Используйте её в группе клуба для проверки статуса синхронизации."
        )
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # Verify user is admin
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ["administrator", "creator"]:
            await message.reply_text(
                "⛔ Только администраторы группы могут использовать эту команду."
            )
            return
    except TelegramError as e:
        logger.error(f"Error checking admin status: {e}")
        await message.reply_text("Не удалось проверить права доступа.")
        return

    # Find club
    with ClubStorage() as cs:
        club = cs.get_club_by_telegram_chat_id(chat_id)
        if not club:
            await message.reply_text(
                "❌ Эта группа не связана с клубом.\n\n"
                "Используйте /create_club чтобы создать клуб."
            )
            return

    # Get current Telegram count (minus 1 for the bot itself)
    try:
        raw_count = await context.bot.get_chat_member_count(chat_id)
        tg_count = max(0, raw_count - 1)  # Exclude bot from count
    except TelegramError as e:
        logger.error(f"Error getting member count: {e}")
        tg_count = club.telegram_member_count or 0

    # Get our counts
    with MembershipStorage() as ms:
        active_count = ms.get_active_members_count(club.id)
        pending_members = ms.get_members_by_status(club.id, MembershipStatus.PENDING)
        pending_count = len(pending_members)
        left_members = ms.get_members_by_status(club.id, MembershipStatus.LEFT)
        left_count = len(left_members)
        kicked_members = ms.get_members_by_status(club.id, MembershipStatus.KICKED)
        kicked_count = len(kicked_members)

    # Update Telegram count in DB
    with ClubStorage() as cs:
        old_count = club.telegram_member_count or 0

        # Update count
        cs.update_telegram_member_count(club.id, tg_count)

        # Reset sync if TG count increased significantly
        if tg_count > old_count and club.sync_completed:
            cs.reset_sync_status(club.id)
            sync_reset = True
        else:
            sync_reset = False

    # Calculate sync percentage
    total_registered = active_count + pending_count
    sync_percent = round(total_registered / tg_count * 100) if tg_count > 0 else 0

    # Determine status emoji
    if sync_percent >= 90:
        status_emoji = "✅"
        status_text = "Отлично!"
    elif sync_percent >= 50:
        status_emoji = "🔄"
        status_text = "Идёт синхронизация..."
    else:
        status_emoji = "⏳"
        status_text = "Ожидание регистрации"

    # Build response
    response = (
        f"📊 Статус клуба \"{club.name}\"\n\n"
        f"👥 В Telegram группе: {tg_count}\n"
        f"✅ Активных в Ayda: {active_count}\n"
        f"⏳ Ожидают активации: {pending_count}\n"
    )

    if left_count > 0:
        response += f"📤 Вышли: {left_count}\n"

    if kicked_count > 0:
        response += f"🚫 Исключены: {kicked_count}\n"

    response += f"\n{status_emoji} Синхронизация: {sync_percent}% — {status_text}"

    if sync_reset:
        response += "\n\n🔄 Обнаружены новые участники, синхронизация возобновлена."

    if tg_count != old_count and old_count > 0:
        diff = tg_count - old_count
        sign = "+" if diff > 0 else ""
        response += f"\n\n📈 Изменение: {sign}{diff} участников"

    await message.reply_text(response)


def get_sync_handlers():
    """Return handlers for sync command."""
    return [
        CommandHandler("sync", handle_sync_command),
    ]
