"""
Tests for Member Sync functionality

Tests cache operations, membership status tracking, and sync logic.
"""

import pytest
from bot.cache import (
    is_member_cached, add_member_to_cache, remove_member_from_cache,
    clear_all_caches, is_sync_completed, mark_sync_completed,
    get_club_from_cache, set_club_in_cache, get_cache_stats
)


class TestMemberCache:
    """Tests for member cache operations."""

    def setup_method(self):
        """Clear caches before each test."""
        clear_all_caches()

    def test_member_not_cached_initially(self):
        """Member should not be in cache initially."""
        assert not is_member_cached(123, 456)

    def test_add_member_to_cache(self):
        """Adding member to cache should make them cached."""
        add_member_to_cache(123, 456)
        assert is_member_cached(123, 456)

    def test_remove_member_from_cache(self):
        """Removing member from cache should work."""
        add_member_to_cache(123, 456)
        assert is_member_cached(123, 456)

        remove_member_from_cache(123, 456)
        assert not is_member_cached(123, 456)

    def test_different_chats_are_separate(self):
        """Members in different chats should be cached separately."""
        add_member_to_cache(100, 1)
        add_member_to_cache(200, 1)

        assert is_member_cached(100, 1)
        assert is_member_cached(200, 1)

        remove_member_from_cache(100, 1)
        assert not is_member_cached(100, 1)
        assert is_member_cached(200, 1)  # Should still be cached

    def test_different_users_are_separate(self):
        """Different users in same chat should be cached separately."""
        add_member_to_cache(123, 1)
        add_member_to_cache(123, 2)

        assert is_member_cached(123, 1)
        assert is_member_cached(123, 2)


class TestClubCache:
    """Tests for club cache operations."""

    def setup_method(self):
        """Clear caches before each test."""
        clear_all_caches()

    def test_club_not_cached_initially(self):
        """Club should not be in cache initially."""
        assert get_club_from_cache(123) is None

    def test_set_and_get_club(self):
        """Setting and getting club should work."""
        set_club_in_cache(123, "club-uuid-123", sync_completed=False)

        club_info = get_club_from_cache(123)
        assert club_info is not None
        assert club_info["club_id"] == "club-uuid-123"
        assert club_info["sync_completed"] is False

    def test_sync_completed_flag(self):
        """Sync completed flag should work correctly."""
        set_club_in_cache(123, "club-uuid", sync_completed=True)

        assert is_sync_completed(123) is True

    def test_sync_not_completed_by_default(self):
        """Sync should not be completed by default."""
        set_club_in_cache(123, "club-uuid")

        assert is_sync_completed(123) is False

    def test_mark_sync_completed(self):
        """Marking sync as completed should work."""
        set_club_in_cache(123, "club-uuid", sync_completed=False)
        assert is_sync_completed(123) is False

        mark_sync_completed(123)
        assert is_sync_completed(123) is True

    def test_mark_sync_completed_for_non_cached_club(self):
        """Marking sync for non-cached club should not crash."""
        # Should not raise an exception
        mark_sync_completed(999)
        assert is_sync_completed(999) is False


class TestCacheStats:
    """Tests for cache statistics."""

    def setup_method(self):
        """Clear caches before each test."""
        clear_all_caches()

    def test_initial_stats(self):
        """Initial stats should be zero."""
        stats = get_cache_stats()
        assert stats["members_cache_size"] == 0
        assert stats["entities_cache_size"] == 0

    def test_stats_after_adding_members(self):
        """Stats should reflect added members."""
        add_member_to_cache(1, 1)
        add_member_to_cache(1, 2)
        add_member_to_cache(2, 1)

        stats = get_cache_stats()
        assert stats["members_cache_size"] == 3

    def test_stats_after_adding_clubs(self):
        """Stats should reflect added clubs."""
        set_club_in_cache(1, "club-1")
        set_club_in_cache(2, "club-2")

        stats = get_cache_stats()
        assert stats["entities_cache_size"] == 2

    def test_clear_all_caches(self):
        """Clearing caches should reset stats."""
        add_member_to_cache(1, 1)
        set_club_in_cache(1, "club-1")

        stats = get_cache_stats()
        assert stats["members_cache_size"] > 0
        assert stats["entities_cache_size"] > 0

        clear_all_caches()

        stats = get_cache_stats()
        assert stats["members_cache_size"] == 0
        assert stats["entities_cache_size"] == 0


class TestMembershipStatus:
    """Tests for membership status enum values."""

    def test_membership_status_values(self):
        """Test all membership status values exist."""
        from storage.db import MembershipStatus

        assert MembershipStatus.PENDING.value == "pending"
        assert MembershipStatus.ACTIVE.value == "active"
        assert MembershipStatus.LEFT.value == "left"
        assert MembershipStatus.KICKED.value == "kicked"
        assert MembershipStatus.BANNED.value == "banned"
        assert MembershipStatus.ARCHIVED.value == "archived"

    def test_membership_source_values(self):
        """Test all membership source values exist."""
        from storage.db import MembershipSource

        assert MembershipSource.ADMIN_IMPORT.value == "admin_import"
        assert MembershipSource.CHAT_MEMBER_EVENT.value == "chat_member_event"
        assert MembershipSource.MESSAGE_ACTIVITY.value == "message_activity"
        assert MembershipSource.MANUAL_REGISTRATION.value == "manual"
        assert MembershipSource.DEEP_LINK.value == "deep_link"
