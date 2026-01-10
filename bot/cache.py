"""
In-memory cache for Telegram member tracking.

Reduces database queries by 99% for message-based sync.
Uses TTLCache to automatically expire entries after 1 hour.

Usage:
    from bot.cache import is_member_cached, add_member_to_cache

    # Check if member is already known
    if is_member_cached(chat_id, user_id):
        return  # Skip DB query

    # After registering member in DB
    add_member_to_cache(chat_id, user_id)
"""

from cachetools import TTLCache
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Cache: "{chat_id}:{user_id}" -> True (member exists in our DB)
# maxsize=50000 supports ~50 groups with 1000 members each
# ttl=3600 (1 hour) ensures fresh data while reducing DB load
_members_cache: TTLCache = TTLCache(maxsize=50000, ttl=3600)

# Cache: chat_id -> {"entity_type": "club"|"group", "entity_id": str, "sync_completed": bool}
# Avoids DB lookup for every message to find club/group by telegram_chat_id
_entities_cache: TTLCache = TTLCache(maxsize=1000, ttl=3600)

# Legacy alias for backward compatibility
_clubs_cache = _entities_cache


# ============= Member Cache =============

def is_member_cached(chat_id: int, user_id: int) -> bool:
    """
    Check if member is in cache (already known to our system).

    Args:
        chat_id: Telegram chat ID
        user_id: Telegram user ID

    Returns:
        True if member is cached, False otherwise
    """
    cache_key = f"{chat_id}:{user_id}"
    return cache_key in _members_cache


def add_member_to_cache(chat_id: int, user_id: int) -> None:
    """
    Add member to cache after DB registration.

    Args:
        chat_id: Telegram chat ID
        user_id: Telegram user ID
    """
    cache_key = f"{chat_id}:{user_id}"
    _members_cache[cache_key] = True
    logger.debug(f"Cache: added member {cache_key}")


def remove_member_from_cache(chat_id: int, user_id: int) -> None:
    """
    Remove member from cache (when they leave group).

    Args:
        chat_id: Telegram chat ID
        user_id: Telegram user ID
    """
    cache_key = f"{chat_id}:{user_id}"
    _members_cache.pop(cache_key, None)
    logger.debug(f"Cache: removed member {cache_key}")


# ============= Entity Cache (Club or Group) =============

def get_entity_from_cache(chat_id: int) -> Optional[dict]:
    """
    Get entity (club or group) info by Telegram chat_id from cache.

    Args:
        chat_id: Telegram chat ID

    Returns:
        Dict with entity_type, entity_id, and sync_completed, or None if not cached
    """
    return _entities_cache.get(chat_id)


def set_entity_in_cache(
    chat_id: int,
    entity_id: str,
    entity_type: str = "club",
    sync_completed: bool = False
) -> None:
    """
    Cache entity (club or group) info for chat_id.

    Args:
        chat_id: Telegram chat ID
        entity_id: Our internal club/group UUID
        entity_type: "club" or "group"
        sync_completed: Whether all members have been synced
    """
    _entities_cache[chat_id] = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "club_id": entity_id if entity_type == "club" else None,  # Legacy compatibility
        "group_id": entity_id if entity_type == "group" else None,
        "sync_completed": sync_completed
    }
    logger.debug(f"Cache: added {entity_type} {chat_id} -> {entity_id}")


# Legacy compatibility functions
def get_club_from_cache(chat_id: int) -> Optional[dict]:
    """Legacy: Get club info from cache."""
    return get_entity_from_cache(chat_id)


def set_club_in_cache(chat_id: int, club_id: str, sync_completed: bool = False) -> None:
    """Legacy: Cache club info."""
    set_entity_in_cache(chat_id, club_id, "club", sync_completed)


def is_sync_completed(chat_id: int) -> bool:
    """
    Check if sync is completed for this entity (club or group).

    When sync is completed, we skip message parsing to reduce unnecessary processing.

    Args:
        chat_id: Telegram chat ID

    Returns:
        True if sync completed, False otherwise
    """
    entity_info = _entities_cache.get(chat_id)
    return entity_info.get("sync_completed", False) if entity_info else False


def mark_sync_completed(chat_id: int) -> None:
    """
    Mark sync as completed for this entity.

    Args:
        chat_id: Telegram chat ID
    """
    entity_info = _entities_cache.get(chat_id)
    if entity_info:
        entity_info["sync_completed"] = True
        logger.info(f"Cache: sync completed for chat {chat_id}")


def reset_sync_status(chat_id: int) -> None:
    """
    Reset sync status (when new members detected in TG).

    Args:
        chat_id: Telegram chat ID
    """
    entity_info = _entities_cache.get(chat_id)
    if entity_info:
        entity_info["sync_completed"] = False
        logger.info(f"Cache: sync reset for chat {chat_id}")


# ============= Cache Management =============

def clear_all_caches() -> None:
    """Clear all caches (for testing or restart)."""
    _members_cache.clear()
    _entities_cache.clear()
    logger.info("Cache: all caches cleared")


def get_cache_stats() -> dict:
    """
    Get cache statistics for monitoring.

    Returns:
        Dict with cache sizes and limits
    """
    return {
        "members_cache_size": len(_members_cache),
        "members_cache_maxsize": _members_cache.maxsize,
        "members_cache_ttl": _members_cache.ttl,
        "entities_cache_size": len(_entities_cache),
        "entities_cache_maxsize": _entities_cache.maxsize,
        "entities_cache_ttl": _entities_cache.ttl,
    }
