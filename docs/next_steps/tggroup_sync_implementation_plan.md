# Telegram Group Member Sync - Implementation Plan

## Overview

Реализация автоматической синхронизации участников Telegram групп с базой данных Ayda Run.
Адаптировано под текущую архитектуру: **SQLAlchemy + SQLite**.

---

## Membership Lifecycle (Жизненный цикл участника)

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    ▼                                         │
┌─────────┐    ┌─────────┐    ┌─────────┐                    │
│ PENDING │───▶│ ACTIVE  │───▶│  LEFT   │────────────────────┘
└─────────┘    └─────────┘    └─────────┘     (может вернуться)
     │              │              │
     │              │              ▼
     │              │         ┌─────────┐
     │              │         │ KICKED  │────────────────────┐
     │              │         └─────────┘                    │
     │              │              │                         │
     │              │              ▼                         │
     │              │         ┌─────────┐                    │
     │              │         │ BANNED  │                    │
     │              │         └─────────┘                    │
     │              │                                        │
     │              ▼                                        │
     │         ┌──────────┐                                  │
     └────────▶│ ARCHIVED │◀─────────────────────────────────┘
               └──────────┘
                (мягкое удаление, долго неактивен)
```

### Статусы и их значения:

| Status | Описание | Когда устанавливается | Может вернуться? |
|--------|----------|----------------------|------------------|
| `PENDING` | Обнаружен, но не активирован | Спарсили из сообщения, ещё не прошёл onboarding | Да → ACTIVE |
| `ACTIVE` | Активный участник | Зарегистрировался, состоит в группе | - |
| `LEFT` | Сам вышел из группы | `chat_member` event: status=left | Да → ACTIVE |
| `KICKED` | Исключён админом | `chat_member` event: status=kicked | Да → ACTIVE |
| `BANNED` | Забанен в группе | `chat_member` event: status=banned | Да* (если разбанят) |
| `ARCHIVED` | В архиве | Долго неактивен (>90 дней) или по запросу | Да → ACTIVE |

**Важно:** Ни один статус не означает удаление данных. При возвращении участника статус меняется обратно на `ACTIVE`, сохраняя историю.

### Переходы статусов:

```python
# Пользователь вернулся в группу
if membership.status in [PENDING, LEFT, KICKED, BANNED, ARCHIVED]:
    membership.status = ACTIVE
    membership.left_at = None
    membership.last_seen = now()

# Пользователь вышел/исключён
if new_telegram_status == "left":
    membership.status = LEFT
    membership.left_at = now()

# Автоматическая архивация (cron job, future)
if membership.last_seen < (now() - 90 days) and membership.status == ACTIVE:
    membership.status = ARCHIVED
```

---

## Phase 1: Database Schema Updates ✅ DONE

> **Completed:** 2024-12-22
> **Commit:** `f5cf41b`
> **Migration:** `migrations/001_add_membership_sync_fields.py`

### 1.1 Добавить новые Enum'ы в `storage/db.py`

```python
class MembershipStatus(str, Enum):
    """Membership status in club/group"""
    PENDING = "pending"      # Detected but not activated yet
    ACTIVE = "active"        # Active member
    LEFT = "left"            # Left voluntarily
    KICKED = "kicked"        # Removed by admin
    BANNED = "banned"        # Banned from group
    ARCHIVED = "archived"    # Soft-deleted / inactive for too long

class MembershipSource(str, Enum):
    """How member was added"""
    ADMIN_IMPORT = "admin_import"           # Parsed from getChatAdministrators
    CHAT_MEMBER_EVENT = "chat_member_event" # chat_member webhook event
    MESSAGE_ACTIVITY = "message_activity"   # Passive tracking from messages
    MANUAL_REGISTRATION = "manual"          # User clicked "Join" button
    DEEP_LINK = "deep_link"                 # Joined via t.me/bot?start=join_xxx
```

### 1.2 Расширить модель `Membership`

```python
class Membership(Base):
    __tablename__ = 'memberships'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)

    club_id = Column(String(36), ForeignKey('clubs.id'), nullable=True, index=True)
    group_id = Column(String(36), ForeignKey('groups.id'), nullable=True, index=True)

    role = Column(SQLEnum(UserRole), default=UserRole.MEMBER, nullable=False)

    # NEW: Sync tracking fields
    status = Column(SQLEnum(MembershipStatus), default=MembershipStatus.ACTIVE, nullable=False, index=True)
    source = Column(SQLEnum(MembershipSource), default=MembershipSource.MANUAL_REGISTRATION, nullable=False)
    last_seen = Column(DateTime, nullable=True)

    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)  # When user left/was kicked

    # Relationships...
```

### 1.3 Добавить sync-поля в модель `Club`

```python
class Club(Base):
    # ... existing fields ...

    # NEW: Sync metadata
    bot_is_admin = Column(Boolean, default=False, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    telegram_member_count = Column(Integer, nullable=True)  # From Telegram API (total in TG group)
    sync_completed = Column(Boolean, default=False, nullable=False)  # All members collected?
```

### 1.4 Миграция базы данных

```bash
# Создать миграцию (если используем Alembic)
alembic revision --autogenerate -m "Add membership sync fields"
alembic upgrade head

# Или для простого случая - пересоздать таблицы
# python -c "from storage.db import init_db; init_db()"
```

**Файлы:**
- [x] `storage/db.py` - добавить enums и поля
- [x] `migrations/001_add_membership_sync_fields.py` - миграция для существующих БД

---

## Phase 2: Cache Layer ✅ DONE

> **Completed:** 2024-12-22
> **Commit:** `f5cf41b`

### 2.1 Создать модуль кеширования `bot/cache.py`

```python
"""
In-memory cache for Telegram member tracking.
Reduces database queries by 99% for message-based sync.
"""

from cachetools import TTLCache
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Cache: "{chat_id}:{user_id}" -> True (member exists in our DB)
_members_cache: TTLCache = TTLCache(maxsize=50000, ttl=3600)  # 1 hour

# Cache: chat_id -> {"club_id": str, "sync_completed": bool}
_clubs_cache: TTLCache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour


def is_member_cached(chat_id: int, user_id: int) -> bool:
    """Check if member is in cache (already known to our system)."""
    cache_key = f"{chat_id}:{user_id}"
    return cache_key in _members_cache


def add_member_to_cache(chat_id: int, user_id: int) -> None:
    """Add member to cache after DB registration."""
    cache_key = f"{chat_id}:{user_id}"
    _members_cache[cache_key] = True
    logger.debug(f"Added to cache: {cache_key}")


def remove_member_from_cache(chat_id: int, user_id: int) -> None:
    """Remove member from cache (when they leave)."""
    cache_key = f"{chat_id}:{user_id}"
    _members_cache.pop(cache_key, None)
    logger.debug(f"Removed from cache: {cache_key}")


def get_club_from_cache(chat_id: int) -> Optional[dict]:
    """Get club info by Telegram chat_id from cache."""
    return _clubs_cache.get(chat_id)


def set_club_in_cache(chat_id: int, club_id: str, sync_completed: bool = False) -> None:
    """Cache club info for chat_id."""
    _clubs_cache[chat_id] = {
        "club_id": club_id,
        "sync_completed": sync_completed
    }


def is_sync_completed(chat_id: int) -> bool:
    """Check if sync is completed for this club (skip message parsing)."""
    club_info = _clubs_cache.get(chat_id)
    return club_info.get("sync_completed", False) if club_info else False


def mark_sync_completed(chat_id: int) -> None:
    """Mark sync as completed for this club."""
    club_info = _clubs_cache.get(chat_id)
    if club_info:
        club_info["sync_completed"] = True


def clear_all_caches() -> None:
    """Clear all caches (for testing or restart)."""
    _members_cache.clear()
    _clubs_cache.clear()
    logger.info("All caches cleared")


def get_cache_stats() -> dict:
    """Get cache statistics for monitoring."""
    return {
        "members_cache_size": len(_members_cache),
        "members_cache_maxsize": _members_cache.maxsize,
        "clubs_cache_size": len(_clubs_cache),
        "clubs_cache_maxsize": _clubs_cache.maxsize,
    }
```

**Файлы:**
- [x] `bot/cache.py` - создать новый файл
- [x] `requirements.txt` - добавить cachetools>=5.3.0

---

## Phase 3: Member Sync Handler

### 3.1 Создать `bot/member_sync_handler.py`

```python
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

from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import ContextTypes, ChatMemberHandler, MessageHandler, filters
from telegram.error import TelegramError

from storage.db import SessionLocal, User, Membership, MembershipStatus, MembershipSource, UserRole
from storage.user_storage import UserStorage
from storage.club_storage import ClubStorage
from storage.membership_storage import MembershipStorage
from bot.cache import (
    is_member_cached, add_member_to_cache, remove_member_from_cache,
    get_club_from_cache, set_club_in_cache, is_sync_completed, mark_sync_completed
)

logger = logging.getLogger(__name__)


# ============= STRATEGY 1: Admin Import =============

async def import_group_admins(bot, chat_id: int, club_id: str) -> int:
    """
    Import all administrators from Telegram group.
    Called when bot is added to group as admin.

    Returns: Number of admins imported
    """
    try:
        admins = await bot.get_chat_administrators(chat_id)
        imported = 0

        with MembershipStorage() as ms:
            with UserStorage() as us:
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

async def handle_join_deep_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start join_{chat_id} command.
    User clicked "Register" button in group.
    """
    if not update.message or not update.message.text:
        return

    args = update.message.text.split()
    if len(args) < 2 or not args[1].startswith("join_"):
        return

    try:
        chat_id = int(args[1].replace("join_", ""))
    except ValueError:
        await update.message.reply_text("Invalid link.")
        return

    user = update.effective_user

    # Verify user is actually in the group
    try:
        member = await context.bot.get_chat_member(chat_id, user.id)
        if member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text("You are not a member of this group.")
            return
    except TelegramError:
        await update.message.reply_text("Could not verify group membership.")
        return

    # Find club by chat_id
    with ClubStorage() as cs:
        club = cs.get_club_by_telegram_chat_id(chat_id)
        if not club:
            await update.message.reply_text("This group is not registered as a club.")
            return

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
        _check_and_update_sync_status(ms, cs, club.id, chat_id)

    add_member_to_cache(chat_id, user.id)

    await update.message.reply_text(
        f"Welcome to {club.name}!\n"
        f"Open Ayda Run to see upcoming activities."
    )


# ============= STRATEGY 3: Chat Member Events =============

async def handle_chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle chat_member events (user joins/leaves group).
    Requires bot to be admin with appropriate permissions.
    """
    if not update.chat_member:
        return

    chat_id = update.chat_member.chat.id
    user = update.chat_member.new_chat_member.user
    new_status = update.chat_member.new_chat_member.status

    if user.is_bot:
        return

    # Check if this chat is a registered club
    club_info = get_club_from_cache(chat_id)
    if not club_info:
        with ClubStorage() as cs:
            club = cs.get_club_by_telegram_chat_id(chat_id)
            if not club:
                return
            set_club_in_cache(chat_id, club.id, club.sync_completed)
            club_info = {"club_id": club.id}

    club_id = club_info["club_id"]

    # User joined
    if new_status in ["member", "administrator", "creator"]:
        await _handle_member_joined(
            chat_id=chat_id,
            club_id=club_id,
            telegram_user=user,
            is_admin=(new_status in ["administrator", "creator"]),
            bot=context.bot
        )

    # User left
    elif new_status in ["left", "kicked", "banned"]:
        await _handle_member_left(
            chat_id=chat_id,
            club_id=club_id,
            telegram_id=user.id,
            status=new_status
        )


async def _handle_member_joined(chat_id: int, club_id: str, telegram_user, is_admin: bool, bot) -> None:
    """Process new member joining the group."""

    with UserStorage() as us:
        user = us.get_or_create_user(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name
        )

    role = UserRole.ORGANIZER if is_admin else UserRole.MEMBER

    with MembershipStorage() as ms:
        ms.add_member_to_club_with_source(
            user_id=user.id,
            club_id=club_id,
            role=role,
            source=MembershipSource.CHAT_MEMBER_EVENT
        )

    add_member_to_cache(chat_id, telegram_user.id)

    # Try to send welcome DM (optional)
    try:
        await bot.send_message(
            telegram_user.id,
            f"Welcome! You've been added to a club.\n"
            f"Open Ayda Run to see activities."
        )
    except TelegramError as e:
        logger.debug(f"Can't send DM to {telegram_user.id}: {e}")


async def _handle_member_left(chat_id: int, club_id: str, telegram_id: int, status: str) -> None:
    """Process member leaving the group."""

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
        ms.mark_member_inactive(
            user_id=user.id,
            club_id=club_id,
            status=membership_status
        )

    remove_member_from_cache(chat_id, telegram_id)
    logger.info(f"Member {telegram_id} marked as {status} in club {club_id}")


# ============= STRATEGY 4: Message Activity =============

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Passive member tracking through message activity.
    Uses cache to minimize DB queries.

    OPTIMIZATION: Skips processing if sync_completed=True for this club.
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

    # Fast path 1: check if sync already completed for this club
    if is_sync_completed(chat_id):
        return

    # Fast path 2: check member cache (<1ms)
    if is_member_cached(chat_id, user_id):
        return

    # Check if this chat is a registered club
    club_info = get_club_from_cache(chat_id)
    if club_info is None:
        with ClubStorage() as cs:
            club = cs.get_club_by_telegram_chat_id(chat_id)
            if not club:
                # Not a registered club
                return
            set_club_in_cache(chat_id, club.id, club.sync_completed)
            club_info = {"club_id": club.id, "sync_completed": club.sync_completed}

            # If sync already completed, skip
            if club.sync_completed:
                return

    club_id = club_info["club_id"]

    # Check DB (slow path)
    with UserStorage() as us:
        user = us.get_user_by_telegram_id(user_id)
        if user:
            with MembershipStorage() as ms:
                if ms.is_member_of_club(user.id, club_id):
                    # Already in DB, add to cache
                    add_member_to_cache(chat_id, user_id)
                    return

    # New member! Register in background
    asyncio.create_task(
        _register_member_from_message(
            chat_id=chat_id,
            club_id=club_id,
            telegram_user=message.from_user
        )
    )

    # Immediately add to cache to prevent duplicate processing
    add_member_to_cache(chat_id, user_id)


async def _register_member_from_message(chat_id: int, club_id: str, telegram_user) -> None:
    """Background task to register member detected from message."""
    try:
        with UserStorage() as us:
            user = us.get_or_create_user(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name
            )

        with MembershipStorage() as ms:
            with ClubStorage() as cs:
                ms.add_member_to_club_with_source(
                    user_id=user.id,
                    club_id=club_id,
                    role=UserRole.MEMBER,
                    source=MembershipSource.MESSAGE_ACTIVITY,
                    status=MembershipStatus.PENDING  # Not fully onboarded yet
                )

                # Check if sync completed after this registration
                _check_and_update_sync_status(ms, cs, club_id, chat_id)

        logger.info(f"Registered member {telegram_user.id} from message in {chat_id}")

    except Exception as e:
        logger.error(f"Failed to register member from message: {e}")


def _check_and_update_sync_status(ms: MembershipStorage, cs: ClubStorage, club_id: str, chat_id: int) -> None:
    """Check if all members are collected and update sync status."""
    club = cs.get_club_by_id(club_id)
    if not club or not club.telegram_member_count:
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
```

**Файлы:**
- [ ] `bot/member_sync_handler.py` - создать новый файл

---

## Phase 4: Storage Layer Updates

### 4.1 Обновить `storage/membership_storage.py`

Добавить новые методы:

```python
def add_member_to_club_with_source(
    self,
    user_id: str,
    club_id: str,
    role: UserRole = UserRole.MEMBER,
    source: MembershipSource = MembershipSource.MANUAL_REGISTRATION,
    status: MembershipStatus = MembershipStatus.ACTIVE
) -> Optional[Membership]:
    """Add member with source tracking."""
    try:
        existing = self.session.query(Membership).filter(
            Membership.user_id == user_id,
            Membership.club_id == club_id
        ).first()

        if existing:
            # Reactivate if was inactive
            if existing.status != MembershipStatus.ACTIVE:
                existing.status = MembershipStatus.ACTIVE
                existing.left_at = None
                existing.last_seen = datetime.utcnow()
                self.session.commit()
            return existing

        membership = Membership(
            user_id=user_id,
            club_id=club_id,
            role=role,
            source=source,
            status=status,
            last_seen=datetime.utcnow()
        )
        self.session.add(membership)
        self.session.commit()
        return membership

    except Exception as e:
        self.session.rollback()
        logger.error(f"Error in add_member_to_club_with_source: {e}")
        raise


def mark_member_inactive(
    self,
    user_id: str,
    club_id: str,
    status: MembershipStatus = MembershipStatus.LEFT
) -> bool:
    """Mark member as inactive (left/kicked/banned)."""
    try:
        membership = self.session.query(Membership).filter(
            Membership.user_id == user_id,
            Membership.club_id == club_id
        ).first()

        if not membership:
            return False

        membership.status = status
        membership.left_at = datetime.utcnow()
        self.session.commit()
        return True

    except Exception as e:
        self.session.rollback()
        logger.error(f"Error in mark_member_inactive: {e}")
        return False


def update_last_seen(self, user_id: str, club_id: str) -> None:
    """Update last_seen timestamp for member."""
    try:
        self.session.query(Membership).filter(
            Membership.user_id == user_id,
            Membership.club_id == club_id
        ).update({"last_seen": datetime.utcnow()})
        self.session.commit()
    except Exception as e:
        self.session.rollback()
        logger.error(f"Error updating last_seen: {e}")


def get_members_count(self, club_id: str, exclude_archived: bool = False) -> int:
    """Get count of members in club."""
    query = self.session.query(Membership).filter(
        Membership.club_id == club_id
    )
    if exclude_archived:
        query = query.filter(Membership.status != MembershipStatus.ARCHIVED)
    return query.count()


def get_active_members_count(self, club_id: str) -> int:
    """Get count of active members in club."""
    return self.session.query(Membership).filter(
        Membership.club_id == club_id,
        Membership.status == MembershipStatus.ACTIVE
    ).count()


def get_members_by_status(self, club_id: str, status: MembershipStatus) -> List[Membership]:
    """Get all members with specific status."""
    return self.session.query(Membership).filter(
        Membership.club_id == club_id,
        Membership.status == status
    ).all()


def get_members_by_source(self, club_id: str, source: MembershipSource) -> List[Membership]:
    """Get all members by source (for analytics)."""
    return self.session.query(Membership).filter(
        Membership.club_id == club_id,
        Membership.source == source
    ).all()
```

### 4.2 Обновить `storage/club_storage.py`

Добавить методы для sync:

```python
def update_telegram_member_count(self, club_id: str, count: int) -> None:
    """Update Telegram member count from API."""
    try:
        self.session.query(Club).filter(Club.id == club_id).update({
            "telegram_member_count": count,
            "last_sync_at": datetime.utcnow()
        })
        self.session.commit()
    except Exception as e:
        self.session.rollback()
        logger.error(f"Error updating telegram_member_count: {e}")


def mark_sync_completed(self, club_id: str) -> None:
    """Mark sync as completed for club."""
    try:
        self.session.query(Club).filter(Club.id == club_id).update({
            "sync_completed": True,
            "last_sync_at": datetime.utcnow()
        })
        self.session.commit()
    except Exception as e:
        self.session.rollback()
        logger.error(f"Error marking sync completed: {e}")


def reset_sync_status(self, club_id: str) -> None:
    """Reset sync status (when new members detected in TG)."""
    try:
        self.session.query(Club).filter(Club.id == club_id).update({
            "sync_completed": False
        })
        self.session.commit()
    except Exception as e:
        self.session.rollback()
        logger.error(f"Error resetting sync status: {e}")
```

**Файлы:**
- [ ] `storage/membership_storage.py` - добавить новые методы
- [ ] `storage/club_storage.py` - добавить методы для sync

---

## Phase 5: Webhook & Handler Registration

### 5.1 Обновить `api_server.py`

```python
# В lifespan, после существующих handlers:

# Phase 7: Member sync handlers
from bot.member_sync_handler import get_member_sync_handlers
for handler in get_member_sync_handlers():
    bot_app.add_handler(handler)
logger.info("[SUCCESS] Member sync handlers registered")
```

### 5.2 Обновить webhook allowed_updates

```python
# В lifespan, при set_webhook:
await bot_app.bot.set_webhook(
    url=webhook_url,
    allowed_updates=[
        "message",           # For message-based sync
        "chat_member",       # For join/leave tracking
        "my_chat_member",    # For bot added/removed events
        "callback_query",    # Existing functionality
    ]
)
```

**Файлы:**
- [ ] `api_server.py` - обновить регистрацию handlers и webhook

---

## Phase 6: Welcome Message Updates

### 6.1 Обновить `bot/group_club_creation_handler.py`

После успешного создания клуба:

```python
# 1. Get member count from Telegram
member_count = await context.bot.get_chat_member_count(chat_id)

# 2. Save to club
with ClubStorage() as cs:
    cs.update_telegram_member_count(club.id, member_count)

# 3. Import admins
from bot.member_sync_handler import import_group_admins
imported_count = await import_group_admins(context.bot, chat_id, club.id)

# 4. Send welcome message with registration button
remaining = member_count - imported_count
await context.bot.send_message(
    chat_id,
    text=(
        f"🎉 Club '{club.name}' created!\n\n"
        f"👥 Total in group: {member_count}\n"
        f"✅ Organizers added: {imported_count}\n"
        f"⏳ Remaining: {remaining}\n\n"
        f"Other members can register below:"
    ),
    reply_markup={
        "inline_keyboard": [[
            {
                "text": "🏃 Register in Ayda Run",
                "url": f"https://t.me/{context.bot.username}?start=join_{chat_id}"
            }
        ]]
    }
)
```

**Файлы:**
- [ ] `bot/group_club_creation_handler.py` - добавить import админов и кнопку регистрации

---

## Phase 7: Sync Command

### 7.1 Создать команду `/sync` для организаторов

```python
# bot/sync_handler.py

async def handle_sync_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    /sync - Update club sync status from Telegram.
    Only for organizers/admins in group chats.
    """
    message = update.message
    if not message or message.chat.type not in ["group", "supergroup"]:
        await message.reply_text("This command only works in groups.")
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    # Verify user is admin
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in ["administrator", "creator"]:
            await message.reply_text("Only admins can use this command.")
            return
    except TelegramError:
        return

    # Find club
    with ClubStorage() as cs:
        club = cs.get_club_by_telegram_chat_id(chat_id)
        if not club:
            await message.reply_text("This group is not registered as a club.")
            return

    # Get current Telegram count
    tg_count = await context.bot.get_chat_member_count(chat_id)

    # Get our counts
    with MembershipStorage() as ms:
        active_count = ms.get_active_members_count(club.id)
        pending_count = len(ms.get_members_by_status(club.id, MembershipStatus.PENDING))
        left_count = len(ms.get_members_by_status(club.id, MembershipStatus.LEFT))

    # Update Telegram count
    with ClubStorage() as cs:
        old_count = club.telegram_member_count or 0
        cs.update_telegram_member_count(club.id, tg_count)

        # Reset sync if TG count increased
        if tg_count > old_count and club.sync_completed:
            cs.reset_sync_status(club.id)

    # Calculate sync percentage
    total_registered = active_count + pending_count
    sync_percent = round(total_registered / tg_count * 100) if tg_count > 0 else 0

    status_emoji = "✅" if sync_percent >= 90 else "🔄" if sync_percent >= 50 else "⏳"

    await message.reply_text(
        f"📊 Club Sync Status\n\n"
        f"👥 In Telegram: {tg_count}\n"
        f"✅ Active in Ayda: {active_count}\n"
        f"⏳ Pending: {pending_count}\n"
        f"📤 Left: {left_count}\n\n"
        f"{status_emoji} Sync: {sync_percent}%"
    )


def get_sync_handlers():
    """Return handlers for sync command."""
    from telegram.ext import CommandHandler
    return [
        CommandHandler("sync", handle_sync_command),
    ]
```

**Файлы:**
- [ ] `bot/sync_handler.py` - создать новый файл

---

## Phase 8: Testing

### 8.1 Unit Tests

```python
# tests/test_member_sync.py

import pytest
from bot.cache import (
    is_member_cached, add_member_to_cache,
    remove_member_from_cache, clear_all_caches,
    is_sync_completed, mark_sync_completed
)

def test_cache_operations():
    clear_all_caches()

    # Initially not cached
    assert not is_member_cached(123, 456)

    # Add to cache
    add_member_to_cache(123, 456)
    assert is_member_cached(123, 456)

    # Remove from cache
    remove_member_from_cache(123, 456)
    assert not is_member_cached(123, 456)


def test_sync_completed_flag():
    clear_all_caches()

    # Initially not completed
    assert not is_sync_completed(123)

    # Mark as completed
    mark_sync_completed(123)
    assert is_sync_completed(123)
```

### 8.2 Integration Test

1. Добавить бота в тестовую группу как админа
2. Проверить что админы группы импортированы
3. Отправить сообщение от нового участника
4. Проверить что участник добавлен в БД со статусом PENDING
5. Удалить участника из группы
6. Проверить что статус изменился на `LEFT`
7. Вернуть участника в группу
8. Проверить что статус снова `ACTIVE`

**Файлы:**
- [ ] `tests/test_member_sync.py` - создать тесты

---

## Phase 9: Analytics (Future)

> Это placeholder для будущей реализации. Не входит в MVP.

### Метрики для организатора:

```
📊 Club Analytics

👥 Membership:
├── Total in TG: 45
├── Registered: 43 (96%)
│   ├── Active: 38
│   ├── Pending: 5
│   └── Left: 2
└── Not registered: 2

📈 Registration sources:
├── Admin import: 3
├── Button click: 25
├── Message activity: 12
└── Chat events: 3

🔥 Activity (last 7 days):
├── Active users: 28 (62%)
├── Messages sent: 156
└── Activities joined: 12

📅 Retention:
├── Day 1: 95%
├── Day 7: 78%
└── Day 30: 65%
```

### Команды (future):

- `/club_stats` - полная статистика клуба
- `/members` - список участников с фильтрами
- `/inactive` - список неактивных участников

### API endpoints (future):

- `GET /api/clubs/{id}/analytics` - получить аналитику
- `GET /api/clubs/{id}/members?status=pending` - фильтрация участников

---

## Summary: Files to Create/Modify

### New Files:
1. `bot/cache.py` - In-memory cache layer
2. `bot/member_sync_handler.py` - All sync strategies
3. `bot/sync_handler.py` - /sync command
4. `tests/test_member_sync.py` - Unit tests

### Modified Files:
1. `storage/db.py` - Add enums and model fields
2. `storage/membership_storage.py` - Add new methods
3. `storage/club_storage.py` - Add sync methods
4. `api_server.py` - Register handlers, update webhook
5. `bot/group_club_creation_handler.py` - Admin import, welcome message

---

## Dependencies

```
cachetools>=5.3.0
```

Add to `requirements.txt` if not present.

---

## Rollout Checklist

- [ ] Disable Privacy Mode in @BotFather
- [ ] Deploy database migration
- [ ] Deploy code changes
- [ ] Verify webhook includes `chat_member` updates
- [ ] Test with a real Telegram group
- [ ] Monitor logs for sync activity
- [ ] Check cache stats after 1 hour of operation

---

## Performance Expectations

| Metric | Without Cache | With Cache |
|--------|---------------|------------|
| Messages/day | 5000 | 5000 |
| DB queries | 10000 | ~50 |
| Webhook response | ~300ms | <10ms |
| Load reduction | - | 99% |

---

## Future Improvements (v1.1+)

1. **Redis cache** - For multi-instance deployments
2. **Celery queue** - For background member registration
3. **Batch sync** - Periodic full sync with Telegram
4. **Analytics dashboard** - See Phase 9
5. **Auto-archive** - Cron job to archive inactive members (>90 days)
