"""
Tests for Telegram Bot Onboarding Flows

Tests cover:
- Flow 1: Participant onboarding (start, consent)
- Flow 2: Club/Group invitations (start with invitation link)
- Storage integration tests
- Input validation tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User as TelegramUser, Message, Chat, CallbackQuery
from telegram.ext import ContextTypes

from storage.db import Club, Group, ClubRequestStatus
from storage.user_storage import UserStorage
from storage.club_storage import ClubStorage
from storage.membership_storage import MembershipStorage

from bot.onboarding_handler import (
    start_onboarding,
    handle_consent,
    AWAITING_CONSENT,
    ASKING_PHOTO_VISIBILITY,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object"""
    update = MagicMock(spec=Update)
    update.effective_user = TelegramUser(
        id=123456789,
        first_name="Test",
        last_name="User",
        username="testuser",
        is_bot=False
    )
    update.effective_chat = Chat(id=123456789, type="private")
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.text = "/start"
    update.callback_query = None
    return update


@pytest.fixture
def mock_callback_update(mock_update):
    """Create a mock Update with callback query"""
    mock_update.callback_query = MagicMock(spec=CallbackQuery)
    mock_update.callback_query.answer = AsyncMock()
    mock_update.callback_query.edit_message_text = AsyncMock()
    mock_update.callback_query.message = mock_update.message
    return mock_update


@pytest.fixture
def mock_context():
    """Create a mock Context object"""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context


@pytest.fixture
def db_session_bot(db_engine):
    """Create test database session for bot tests"""
    from sqlalchemy.orm import sessionmaker
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_club(db_session_bot):
    """Create a test club"""
    # Create a user first to be the club creator
    from storage.user_storage import UserStorage
    user_storage = UserStorage(db_session_bot)
    creator = user_storage.get_or_create_user(
        telegram_id=999999,
        username="clubcreator",
        first_name="Club",
        last_name="Creator"
    )

    from app_config.constants import DEFAULT_COUNTRY, DEFAULT_CITY
    club = Club(
        name="Test Running Club",
        description="A club for testing",
        creator_id=creator.id,
        country=DEFAULT_COUNTRY,
        city=DEFAULT_CITY,
    )
    db_session_bot.add(club)
    db_session_bot.flush()  # Use flush instead of commit for transaction
    db_session_bot.refresh(club)
    return club


@pytest.fixture
def test_group(db_session_bot, test_club):
    """Create a test group"""
    from app_config.constants import DEFAULT_COUNTRY, DEFAULT_CITY
    group = Group(
        name="Morning Runners",
        description="Morning running group",
        club_id=test_club.id,
        creator_id=test_club.creator_id,  # Groups require creator_id
        country=DEFAULT_COUNTRY,
        city=DEFAULT_CITY,
    )
    db_session_bot.add(group)
    db_session_bot.flush()  # Use flush instead of commit for transaction
    db_session_bot.refresh(group)
    return group


# ============================================================================
# Flow 1: Participant Onboarding Tests
# ============================================================================

class TestFlow1ParticipantOnboarding:
    """Test Flow 1: Self-registration participant onboarding"""

    @pytest.mark.asyncio
    async def test_start_onboarding_new_user(self, mock_update, mock_context, db_session_bot):
        """Test /start command for a new user"""
        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            result = await start_onboarding(mock_update, mock_context)

            # Should move to AWAITING_CONSENT state
            assert result == AWAITING_CONSENT

            # Should send welcome message
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            assert "Ayda Run" in call_args[0][0] or "приветств" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_handle_consent_accepted(self, mock_callback_update, mock_context, db_session_bot):
        """Test user accepts consent"""
        mock_callback_update.callback_query.data = "consent_yes"

        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            result = await handle_consent(mock_callback_update, mock_context)

            # Should move to ASKING_PHOTO_VISIBILITY state (new step in flow)
            assert result == ASKING_PHOTO_VISIBILITY

            # Should edit message with photo visibility selection
            mock_callback_update.callback_query.edit_message_text.assert_called_once()



# ============================================================================
# Flow 2: Invitation Tests
# ============================================================================

class TestFlow2Invitations:
    """Test Flow 2A/2B: Club and Group invitations"""

    @pytest.mark.asyncio
    async def test_club_invitation_new_user(self, mock_update, mock_context, db_session_bot, test_club):
        """Test club invitation for a new user"""
        # Simulate /start club_<uuid>
        mock_update.message.text = f"/start club_{test_club.id}"
        mock_context.args = [f"club_{test_club.id}"]

        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            result = await start_onboarding(mock_update, mock_context)

            # Should save invitation data
            assert "invitation_type" in mock_context.user_data
            assert mock_context.user_data["invitation_type"] == "club"
            assert mock_context.user_data["invitation_id"] == test_club.id



# ============================================================================
# Storage Tests
# ============================================================================

class TestStorageIntegration:
    """Test storage layer integration with bot flows"""

    def test_user_storage_operations(self, db_session_bot):
        """Test UserStorage methods"""
        storage = UserStorage(db_session_bot)

        # Create user
        user = storage.get_or_create_user(
            telegram_id=999999,
            username="storagetest",
            first_name="Storage",
            last_name="Test"
        )
        assert user.telegram_id == 999999

        # Update sports
        user = storage.update_preferred_sports(user.id, ["running", "cycling"])
        assert "running" in user.preferred_sports

        # Mark onboarding complete
        user = storage.mark_onboarding_complete(user.id)
        assert user.has_completed_onboarding is True

    def test_membership_storage_operations(self, db_session_bot, test_club, test_group):
        """Test MembershipStorage methods"""
        user_storage = UserStorage(db_session_bot)
        membership_storage = MembershipStorage(db_session_bot)

        # Create user
        user = user_storage.get_or_create_user(
            telegram_id=888888,
            username="membertest",
            first_name="Member",
            last_name="Test"
        )

        # Add to club
        membership_storage.add_member_to_club(user.id, test_club.id)
        assert membership_storage.is_member_of_club(user.id, test_club.id) is True

        # Add to group
        membership_storage.add_member_to_group(user.id, test_group.id)
        assert membership_storage.is_member_of_group(user.id, test_group.id) is True

        # Get memberships
        memberships = membership_storage.get_user_memberships(user.id)
        assert len(memberships) >= 2

    def test_club_storage_operations(self, db_session_bot):
        """Test ClubStorage methods"""
        storage = ClubStorage(db_session_bot)
        user_storage = UserStorage(db_session_bot)

        # Create user for request
        user = user_storage.get_or_create_user(
            telegram_id=777777,
            username="clubtest",
            first_name="Club",
            last_name="Test"
        )

        # Create club request
        request_data = {
            "user_id": user.id,
            "name": "Storage Test Club",
            "description": "Test description",
            "sports": '["running"]',
            "members_count": 25,
            "groups_count": 2,
        }
        request = storage.create_club_request(request_data)
        assert request.status == ClubRequestStatus.PENDING

        # Get pending requests
        pending = storage.get_pending_requests()
        assert len(pending) > 0
        assert any(r.id == request.id for r in pending)


# ============================================================================
# Validation Tests
# ============================================================================

class TestValidation:
    """Test bot input validation"""

    def test_club_name_validation(self):
        """Test club name validation"""
        from bot.validators import validate_club_name

        # Valid names
        valid, msg = validate_club_name("Test Running Club")
        assert valid is True

        # Too short
        valid, msg = validate_club_name("AB")
        assert valid is False

        # Too long
        valid, msg = validate_club_name("A" * 300)
        assert valid is False

    def test_members_count_validation(self):
        """Test members count validation"""
        from bot.validators import validate_members_count

        # Valid count
        valid, count = validate_members_count("50")
        assert valid is True
        assert count == 50

        # Invalid format
        valid, count = validate_members_count("not a number")
        assert valid is False

        # Negative number
        valid, count = validate_members_count("-10")
        assert valid is False

    def test_telegram_link_validation(self):
        """Test Telegram link validation"""
        from bot.validators import is_valid_telegram_link

        # Valid links (https format)
        assert is_valid_telegram_link("https://t.me/testgroup") is True
        assert is_valid_telegram_link("http://t.me/testgroup") is True

        # Valid usernames
        assert is_valid_telegram_link("@testgroup") is True

        # Invalid links
        assert is_valid_telegram_link("https://google.com") is False
        assert is_valid_telegram_link("not a link") is False
        assert is_valid_telegram_link("t.me/testgroup") is False  # Missing protocol