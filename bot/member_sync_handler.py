"""
Telegram Group Member Sync Handler

Implements 4 sync strategies:
1. Admin import (getChatAdministrators) - immediate
2. Cold start (manual registration via deep link)
3. Chat member events (join/leave tracking)
4. Message activity (passive tracking with cache)

See docs/next_steps/tggroup_sync_implementation_plan.md for lifecycle details.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes, ChatMemberHandler, MessageHandler, filters
from telegram.error import TelegramError

from storage.db import (
    MembershipStatus, MembershipSource, UserRole
)
from storage.user_storage import UserStorage
from storage.club_storage import ClubStorage
from storage.membership_storage import MembershipStorage
from bot.cache import (
    is_member_cached, add_member_to_cache, remove_member_from_cache,
    get_entity_from_cache, set_entity_in_cache, is_sync_completed, mark_sync_completed,
    # Legacy imports for backward compatibility
    get_club_from_cache, set_club_in_cache
)

logger = logging.getLogger(__name__)


# ============= STRATEGY 1: Admin Import =============

async def import_group_admins(bot, chat_id: int, club_id: str) -> int:
    """
    Import all administrators from Telegram group.
    Called when bot is added to group as admin.

    Args:
        bot: Telegram bot instance
        chat_id: Telegram chat ID
        club_id: Our internal club UUID

    Returns:
        Number of admins imported
    """
    try:
        admins = await bot.get_chat_administrators(chat_id)
        imported = 0

        with UserStorage() as us:
            with MembershipStorage() as ms:
                for admin in admins:
                    if admin.user.is_bot:
                        continue

                    # Create or get user
                    user = us.get_or_create_user(
                        telegram_id=admin.user.id,
                        username=admin.user.username,
                        first_name=admin.user.first_name
                    )

                    # Determine role
                    role = UserRole.ORGANIZER
                    if admin.status == "creator":
                        role = UserRole.ADMIN

                    # Add to club with source tracking
                    ms.add_member_to_club_with_source(
                        user_id=user.id,
                        club_id=club_id,
                        role=role,
                        source=MembershipSource.ADMIN_IMPORT
                    )

                    add_member_to_cache(chat_id, admin.user.id)
                    imported += 1

        logger.info(f"Imported {imported} admins from chat {chat_id}")
        return imported

    except TelegramError as e:
        logger.error(f"Failed to import admins from {chat_id}: {e}")
        return 0


# ============= STRATEGY 2: Cold Start (Deep Link) =============

async def handle_join_deep_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle /start join_{chat_id} command.
    User clicked "Register" button in group.

    Args:
        update: Telegram update
        context: Bot context

    Returns:
        True if handled, False if not a join deep link
    """
    if not update.message or not update.message.text:
        return False

    args = update.message.text.split()
    if len(args) < 2 or not args[1].startswith("join_"):
        return False

    try:
        chat_id = int(args[1].replace("join_", ""))
    except ValueError:
        await update.message.reply_text("Invalid link.")
        return True

    user = update.effective_user

    # Verify user is actually in the group
    try:
        member = await context.bot.get_chat_member(chat_id, user.id)
        if member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text("You are not a member of this group.")
            return True
    except TelegramError:
        await update.message.reply_text("Could not verify group membership.")
        return True

    # Find club by chat_id
    with ClubStorage() as cs:
        club = cs.get_club_by_telegram_chat_id(chat_id)
        if not club:
            await update.message.reply_text("This group is not registered as a club.")
            return True

    # Register user
    with UserStorage() as us:
        db_user = us.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name
        )

    with MembershipStorage() as ms:
        ms.add_member_to_club_with_source(
            user_id=db_user.id,
            club_id=club.id,
            role=UserRole.MEMBER,
            source=MembershipSource.DEEP_LINK
        )

        # Check if sync completed after this registration
        _check_and_update_sync_status(ms, club.id, chat_id)

    add_member_to_cache(chat_id, user.id)

    await update.message.reply_text(
        f"Welcome to {club.name}!\n"
        f"Open Ayda Run to see upcoming activities."
    )
    return True


# ============= STRATEGY 3: Chat Member Events =============

async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle chat_member events (user joins/leaves group).
    Requires bot to be admin with appropriate permissions.
    Supports both clubs and groups.

    Args:
        update: Telegram update
        context: Bot context
    """
    if not update.chat_member:
        return

    chat_id = update.chat_member.chat.id
    user = update.chat_member.new_chat_member.user
    new_status = update.chat_member.new_chat_member.status

    if user.is_bot:
        return

    # Check if this chat is a registered club or group
    entity_info = get_entity_from_cache(chat_id)
    if not entity_info:
        with ClubStorage() as cs:
            # First check for club
            club = cs.get_club_by_telegram_chat_id(chat_id)
            if club:
                set_entity_in_cache(chat_id, club.id, "club", getattr(club, 'sync_completed', False))
                entity_info = {"entity_type": "club", "entity_id": club.id, "club_id": club.id}
            else:
                # Then check for group
                group = cs.get_group_by_telegram_chat_id(chat_id)
                if group:
                    set_entity_in_cache(chat_id, group.id, "group", False)
                    entity_info = {"entity_type": "group", "entity_id": group.id, "group_id": group.id}
                else:
                    return

    entity_type = entity_info.get("entity_type", "club")
    entity_id = entity_info.get("entity_id") or entity_info.get("club_id")

    # User joined
    if new_status in ["member", "administrator", "creator"]:
        await _handle_member_joined(
            chat_id=chat_id,
            entity_id=entity_id,
            entity_type=entity_type,
            telegram_user=user,
            is_admin=(new_status in ["administrator", "creator"]),
            bot=context.bot
        )

    # User left
    elif new_status in ["left", "kicked", "banned"]:
        await _handle_member_left(
            chat_id=chat_id,
            entity_id=entity_id,
            entity_type=entity_type,
            telegram_id=user.id,
            status=new_status
        )


async def _handle_member_joined(
    chat_id: int,
    entity_id: str,
    entity_type: str,
    telegram_user,
    is_admin: bool,
    bot
) -> None:
    """Process new member joining the group. Supports both clubs and groups."""

    with UserStorage() as us:
        user = us.get_or_create_user(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name
        )

    role = UserRole.ORGANIZER if is_admin else UserRole.MEMBER

    with MembershipStorage() as ms:
        if entity_type == "club":
            ms.add_member_to_club_with_source(
                user_id=user.id,
                club_id=entity_id,
                role=role,
                source=MembershipSource.CHAT_MEMBER_EVENT,
                status=MembershipStatus.PENDING
            )
        else:  # group
            ms.add_member_to_group_with_source(
                user_id=user.id,
                group_id=entity_id,
                role=role,
                source=MembershipSource.CHAT_MEMBER_EVENT,
                status=MembershipStatus.PENDING
            )

    add_member_to_cache(chat_id, telegram_user.id)

    logger.info(f"Member {telegram_user.id} joined {entity_type} {entity_id} via chat_member event (PENDING)")


async def _handle_member_left(
    chat_id: int,
    entity_id: str,
    entity_type: str,
    telegram_id: int,
    status: str
) -> None:
    """Process member leaving the group. Supports both clubs and groups."""

    with UserStorage() as us:
        user = us.get_user_by_telegram_id(telegram_id)
        if not user:
            return

    # Map Telegram status to our status
    status_map = {
        "left": MembershipStatus.LEFT,
        "kicked": MembershipStatus.KICKED,
        "banned": MembershipStatus.BANNED,
    }
    membership_status = status_map.get(status, MembershipStatus.LEFT)

    with MembershipStorage() as ms:
        if entity_type == "club":
            ms.mark_member_inactive(
                user_id=user.id,
                club_id=entity_id,
                status=membership_status
            )
        else:  # group
            ms.mark_member_inactive_in_group(
                user_id=user.id,
                group_id=entity_id,
                status=membership_status
            )

    remove_member_from_cache(chat_id, telegram_id)
    logger.info(f"Member {telegram_id} marked as {status} in {entity_type} {entity_id}")


# ============= STRATEGY 4: Message Activity =============

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Passive member tracking through message activity.
    Uses cache to minimize DB queries.
    Supports both clubs and groups.

    OPTIMIZATION: Skips processing if sync_completed=True for this entity.

    Args:
        update: Telegram update
        context: Bot context
    """
    message = update.message
    if not message or not message.from_user:
        return

    # Only process group messages
    if message.chat.type not in ["group", "supergroup"]:
        return

    # Skip bots
    if message.from_user.is_bot:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # Fast path 1: check if sync already completed for this entity
    if is_sync_completed(chat_id):
        return

    # Fast path 2: check member cache (<1ms)
    if is_member_cached(chat_id, user_id):
        return

    # Check if this chat is a registered club or group
    entity_info = get_entity_from_cache(chat_id)
    if entity_info is None:
        with ClubStorage() as cs:
            # First check for club
            club = cs.get_club_by_telegram_chat_id(chat_id)
            if club:
                sync_completed = getattr(club, 'sync_completed', False)
                set_entity_in_cache(chat_id, club.id, "club", sync_completed)
                entity_info = {"entity_type": "club", "entity_id": club.id, "sync_completed": sync_completed}
            else:
                # Then check for group
                group = cs.get_group_by_telegram_chat_id(chat_id)
                if group:
                    set_entity_in_cache(chat_id, group.id, "group", False)
                    entity_info = {"entity_type": "group", "entity_id": group.id, "sync_completed": False}
                else:
                    # Not a registered club or group
                    return

            # If sync already completed, skip
            if entity_info.get("sync_completed"):
                return

    entity_type = entity_info.get("entity_type", "club")
    entity_id = entity_info.get("entity_id") or entity_info.get("club_id")

    # Check DB (slow path)
    with UserStorage() as us:
        user = us.get_user_by_telegram_id(user_id)
        if user:
            with MembershipStorage() as ms:
                if entity_type == "club":
                    if ms.is_member_of_club(user.id, entity_id):
                        add_member_to_cache(chat_id, user_id)
                        return
                else:  # group
                    if ms.is_member_of_group(user.id, entity_id):
                        add_member_to_cache(chat_id, user_id)
                        return

    # New member! Register in background
    asyncio.create_task(
        _register_member_from_message(
            chat_id=chat_id,
            entity_id=entity_id,
            entity_type=entity_type,
            telegram_user=message.from_user
        )
    )

    # Immediately add to cache to prevent duplicate processing
    add_member_to_cache(chat_id, user_id)


async def _register_member_from_message(
    chat_id: int,
    entity_id: str,
    entity_type: str,
    telegram_user
) -> None:
    """Background task to register member detected from message. Supports clubs and groups."""
    try:
        with UserStorage() as us:
            user = us.get_or_create_user(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name
            )

        with MembershipStorage() as ms:
            if entity_type == "club":
                ms.add_member_to_club_with_source(
                    user_id=user.id,
                    club_id=entity_id,
                    role=UserRole.MEMBER,
                    source=MembershipSource.MESSAGE_ACTIVITY,
                    status=MembershipStatus.PENDING
                )
                # Check if sync completed after this registration
                _check_and_update_sync_status(ms, entity_id, chat_id)
            else:  # group
                ms.add_member_to_group_with_source(
                    user_id=user.id,
                    group_id=entity_id,
                    role=UserRole.MEMBER,
                    source=MembershipSource.MESSAGE_ACTIVITY,
                    status=MembershipStatus.PENDING
                )

        logger.info(f"Registered member {telegram_user.id} from message in {entity_type} {entity_id}")

    except Exception as e:
        logger.error(f"Failed to register member from message: {e}")


def _check_and_update_sync_status(ms: MembershipStorage, club_id: str, chat_id: int) -> None:
    """Check if all members are collected and update sync status."""
    with ClubStorage() as cs:
        club = cs.get_club_by_id(club_id)
        if not club or not getattr(club, 'telegram_member_count', None):
            return

        # Count all members (any status except ARCHIVED)
        active_count = ms.get_members_count(club_id, exclude_archived=True)

        if active_count >= club.telegram_member_count:
            cs.mark_sync_completed(club_id)
            mark_sync_completed(chat_id)
            logger.info(f"Sync completed for club {club_id}: {active_count}/{club.telegram_member_count}")


# ============= Handler Registration =============

def get_member_sync_handlers():
    """Return list of handlers for member sync."""
    return [
        # Strategy 3: Chat member events
        ChatMemberHandler(handle_chat_member_update, ChatMemberHandler.CHAT_MEMBER),

        # Strategy 4: Message activity (low priority, group 10)
        MessageHandler(
            filters.ChatType.GROUPS & ~filters.COMMAND,
            handle_group_message,
            block=False  # Non-blocking for performance
        ),
    ]
