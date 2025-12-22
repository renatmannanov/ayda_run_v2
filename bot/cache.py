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

# Cache: chat_id -> {"club_id": str, "sync_completed": bool}
# Avoids DB lookup for every message to find club by telegram_chat_id
_clubs_cache: TTLCache = TTLCache(maxsize=1000, ttl=3600)


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


# ============= Club Cache =============

def get_club_from_cache(chat_id: int) -> Optional[dict]:
    """
    Get club info by Telegram chat_id from cache.

    Args:
        chat_id: Telegram chat ID

    Returns:
        Dict with club_id and sync_completed, or None if not cached
    """
    return _clubs_cache.get(chat_id)


def set_club_in_cache(chat_id: int, club_id: str, sync_completed: bool = False) -> None:
    """
    Cache club info for chat_id.

    Args:
        chat_id: Telegram chat ID
        club_id: Our internal club UUID
        sync_completed: Whether all members have been synced
    """
    _clubs_cache[chat_id] = {
        "club_id": club_id,
        "sync_completed": sync_completed
    }
    logger.debug(f"Cache: added club {chat_id} -> {club_id}")


def is_sync_completed(chat_id: int) -> bool:
    """
    Check if sync is completed for this club.

    When sync is completed, we skip message parsing for this club
    to reduce unnecessary processing.

    Args:
        chat_id: Telegram chat ID

    Returns:
        True if sync completed, False otherwise
    """
    club_info = _clubs_cache.get(chat_id)
    return club_info.get("sync_completed", False) if club_info else False


def mark_sync_completed(chat_id: int) -> None:
    """
    Mark sync as completed for this club.

    Args:
        chat_id: Telegram chat ID
    """
    club_info = _clubs_cache.get(chat_id)
    if club_info:
        club_info["sync_completed"] = True
        logger.info(f"Cache: sync completed for chat {chat_id}")


def reset_sync_status(chat_id: int) -> None:
    """
    Reset sync status for club (when new members detected in TG).

    Args:
        chat_id: Telegram chat ID
    """
    club_info = _clubs_cache.get(chat_id)
    if club_info:
        club_info["sync_completed"] = False
        logger.info(f"Cache: sync reset for chat {chat_id}")


# ============= Cache Management =============

def clear_all_caches() -> None:
    """Clear all caches (for testing or restart)."""
    _members_cache.clear()
    _clubs_cache.clear()
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
        "clubs_cache_size": len(_clubs_cache),
        "clubs_cache_maxsize": _clubs_cache.maxsize,
        "clubs_cache_ttl": _clubs_cache.ttl,
    }
