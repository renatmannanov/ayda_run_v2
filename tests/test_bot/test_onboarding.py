"""
Tests for Telegram Bot Onboarding Flows

Tests cover:
- Flow 1: Participant onboarding (self-registration)
- Flow 2A/2B: Club/Group invitations
- Flow 3: Organizer club creation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User as TelegramUser, Message, Chat, CallbackQuery
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session

from storage.db import User, Club, Group, ClubRequest, ClubRequestStatus, UserRole
from storage.user_storage import UserStorage
from storage.club_storage import ClubStorage
from storage.group_storage import GroupStorage
from storage.membership_storage import MembershipStorage

# Import handlers to test
from bot.onboarding_handler import (
    start_onboarding,
    handle_consent,
    handle_sports_selection,
    handle_role_selection,
    complete_onboarding,
    AWAITING_CONSENT,
    SELECTING_SPORTS,
    SELECTING_ROLE,
    SHOWING_INTRO,
)

from bot.invitation_handler import (
    handle_join_club,
    handle_join_group,
)

from bot.organizer_handler import (
    start_organizer_flow,
    handle_club_name,
    handle_club_description,
    handle_club_sports_selection,
    handle_club_members_count,
    handle_club_groups_count,
    handle_club_telegram_link,
    handle_club_contact_phone,
    handle_club_request_confirm,
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
    db_session_bot.commit()
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
        country=DEFAULT_COUNTRY,
        city=DEFAULT_CITY,
    )
    db_session_bot.add(group)
    db_session_bot.commit()
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
        mock_callback_update.callback_query.data = "consent_accept"

        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            result = await handle_consent(mock_callback_update, mock_context)

            # Should move to SELECTING_SPORTS state
            assert result == SELECTING_SPORTS

            # Should edit message with sports selection
            mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_sports_selection(self, mock_callback_update, mock_context, db_session_bot):
        """Test user selects sports"""
        mock_callback_update.callback_query.data = "sport_running"
        mock_context.user_data = {"selected_sports": []}

        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            result = await handle_sports_selection(mock_callback_update, mock_context)

            # Should store selected sport
            assert "running" in mock_context.user_data.get("selected_sports", [])

    @pytest.mark.asyncio
    async def test_handle_role_selection_participant(self, mock_callback_update, mock_context, db_session_bot):
        """Test user selects participant role"""
        mock_callback_update.callback_query.data = "role_participant"
        mock_context.user_data = {"selected_sports": ["running"]}

        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            result = await handle_role_selection(mock_callback_update, mock_context)

            # Should move to SHOWING_INTRO
            assert result == SHOWING_INTRO

    @pytest.mark.asyncio
    async def test_complete_onboarding(self, mock_callback_update, mock_context, db_session_bot):
        """Test completing onboarding"""
        mock_callback_update.callback_query.data = "intro_done"
        mock_context.user_data = {
            "selected_sports": ["running", "trail"],
            "selected_role": "participant"
        }

        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            result = await complete_onboarding(mock_callback_update, mock_context)

            # Should end conversation
            from telegram.ext import ConversationHandler
            assert result == ConversationHandler.END

            # Check user was created and onboarding completed
            user_storage = UserStorage(db_session_bot)
            user = user_storage.get_user_by_telegram_id(123456789)
            assert user is not None
            assert user.has_completed_onboarding is True


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

    @pytest.mark.asyncio
    async def test_group_invitation_existing_user(self, mock_callback_update, mock_context, db_session_bot, test_group):
        """Test group invitation for existing user"""
        # Create existing user
        user_storage = UserStorage(db_session_bot)
        user = user_storage.get_or_create_user(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        user_storage.mark_onboarding_complete(user.id)

        # Simulate existing user clicking invitation
        mock_callback_update.callback_query.data = "group_join_yes"
        mock_context.user_data = {"invitation_id": test_group.id}

        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            await handle_join_group(mock_callback_update, mock_context)

            # Should add user to group
            membership_storage = MembershipStorage(db_session_bot)
            assert membership_storage.is_member_of_group(user.id, test_group.id) is True

    @pytest.mark.asyncio
    async def test_club_invitation_auto_join_after_onboarding(
        self, mock_callback_update, mock_context, db_session_bot, test_club
    ):
        """Test auto-joining club after completing onboarding via invitation"""
        mock_callback_update.callback_query.data = "intro_done"
        mock_context.user_data = {
            "selected_sports": ["running"],
            "selected_role": "participant",
            "invitation_type": "club",
            "invitation_id": test_club.id
        }

        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            await complete_onboarding(mock_callback_update, mock_context)

            # Check user was added to club
            user_storage = UserStorage(db_session_bot)
            user = user_storage.get_user_by_telegram_id(123456789)

            membership_storage = MembershipStorage(db_session_bot)
            assert membership_storage.is_member_of_club(user.id, test_club.id) is True


# ============================================================================
# Flow 3: Organizer Tests
# ============================================================================

class TestFlow3Organizer:
    """Test Flow 3: Organizer club creation flow"""

    @pytest.mark.asyncio
    async def test_start_organizer_flow(self, mock_callback_update, mock_context, db_session_bot):
        """Test starting organizer flow"""
        mock_callback_update.callback_query.data = "role_organizer"
        mock_context.user_data = {"selected_sports": ["running"]}

        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            result = await handle_role_selection(mock_callback_update, mock_context)

            # Should present organizer type choice
            assert mock_callback_update.callback_query.edit_message_text.called

    @pytest.mark.asyncio
    async def test_club_creation_flow(self, mock_update, mock_context, db_session_bot):
        """Test full club creation form"""
        # Create user first
        user_storage = UserStorage(db_session_bot)
        user = user_storage.get_or_create_user(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User"
        )

        # Test club name input
        mock_update.message.text = "Test Running Club"

        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            result = await handle_club_name(mock_update, mock_context)

            # Should store club name
            assert mock_context.user_data.get("club_name") == "Test Running Club"

    @pytest.mark.asyncio
    async def test_club_request_creation(self, mock_callback_update, mock_context, db_session_bot):
        """Test creating club request"""
        # Create user
        user_storage = UserStorage(db_session_bot)
        user = user_storage.get_or_create_user(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User"
        )

        # Prepare club data
        mock_callback_update.callback_query.data = "club_request_confirm"
        mock_context.user_data = {
            "club_name": "Test Running Club",
            "club_description": "A test club",
            "club_sports": ["running", "trail"],
            "club_members_count": 50,
            "club_groups_count": 3,
            "club_telegram": "https://t.me/testclub",
            "club_contact": "+79991234567"
        }

        with patch('storage.db.SessionLocal', return_value=db_session_bot):
            with patch('bot.admin_notifications.send_club_request_notification'):
                await handle_club_request_confirm(mock_callback_update, mock_context)

                # Check club request was created
                club_storage = ClubStorage(db_session_bot)
                requests = club_storage.get_pending_requests()
                assert len(requests) > 0
                assert requests[0].name == "Test Running Club"
                assert requests[0].status == ClubRequestStatus.PENDING


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

        # Valid links
        assert is_valid_telegram_link("https://t.me/testgroup") is True
        assert is_valid_telegram_link("t.me/testgroup") is True

        # Invalid links
        assert is_valid_telegram_link("https://google.com") is False
        assert is_valid_telegram_link("not a link") is False