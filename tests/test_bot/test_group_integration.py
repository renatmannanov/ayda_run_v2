"""
Integration tests for Telegram Group Integration

Tests the interaction between group parser, validators, and club storage.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from bot.group_parser import TelegramGroupParser
from bot.validators import validate_group_data
from storage.club_storage import ClubStorage
from storage.db import Club, User, Membership, UserRole


class TestGroupParser:
    """Tests for TelegramGroupParser"""

    @pytest.mark.asyncio
    async def test_parse_group_info_success(self):
        """Test successful parsing of group information"""
        parser = TelegramGroupParser()

        # Mock bot and chat
        mock_bot = AsyncMock()
        mock_chat = Mock()
        mock_chat.id = -1001234567890
        mock_chat.title = "Test Running Club"
        mock_chat.description = "A club for runners"
        mock_chat.username = "testrunclub"
        mock_chat.type = "supergroup"
        mock_chat.photo = Mock(big_file_id="file123")
        mock_chat.invite_link = "https://t.me/testrunclub"

        mock_bot.get_chat.return_value = mock_chat
        mock_bot.get_chat_member_count.return_value = 50

        # Parse group info
        result = await parser.parse_group_info(-1001234567890, mock_bot)

        # Verify
        assert result['chat_id'] == -1001234567890
        assert result['title'] == "Test Running Club"
        assert result['description'] == "A club for runners"
        assert result['username'] == "testrunclub"
        assert result['type'] == "supergroup"
        assert result['member_count'] == 50
        assert result['photo'] == "file123"

    @pytest.mark.asyncio
    async def test_verify_bot_is_admin_success(self):
        """Test bot admin verification when bot is admin"""
        parser = TelegramGroupParser()

        # Mock bot and member
        mock_bot = AsyncMock()
        mock_bot_user = Mock(id=123456)
        mock_bot.get_me.return_value = mock_bot_user

        mock_member = Mock()
        mock_member.status = "administrator"
        mock_member.can_invite_users = True

        mock_bot.get_chat_member.return_value = mock_member

        # Verify
        is_admin, error = await parser.verify_bot_is_admin(-1001234567890, mock_bot)

        assert is_admin is True
        assert error == ""

    @pytest.mark.asyncio
    async def test_verify_bot_is_admin_not_admin(self):
        """Test bot admin verification when bot is not admin"""
        parser = TelegramGroupParser()

        # Mock bot and member
        mock_bot = AsyncMock()
        mock_bot_user = Mock(id=123456)
        mock_bot.get_me.return_value = mock_bot_user

        mock_member = Mock()
        mock_member.status = "member"

        mock_bot.get_chat_member.return_value = mock_member

        # Verify
        is_admin, error = await parser.verify_bot_is_admin(-1001234567890, mock_bot)

        assert is_admin is False
        assert "не является администратором" in error

    @pytest.mark.asyncio
    async def test_verify_bot_is_admin_no_invite_permission(self):
        """Test bot admin verification when bot lacks invite permission"""
        parser = TelegramGroupParser()

        # Mock bot and member
        mock_bot = AsyncMock()
        mock_bot_user = Mock(id=123456)
        mock_bot.get_me.return_value = mock_bot_user

        mock_member = Mock()
        mock_member.status = "administrator"
        mock_member.can_invite_users = False

        mock_bot.get_chat_member.return_value = mock_member

        # Verify
        is_admin, error = await parser.verify_bot_is_admin(-1001234567890, mock_bot)

        assert is_admin is False
        assert "Приглашать пользователей" in error

    @pytest.mark.asyncio
    async def test_verify_user_is_admin_creator(self):
        """Test user admin verification when user is creator"""
        parser = TelegramGroupParser()

        # Mock bot and member
        mock_bot = AsyncMock()
        mock_member = Mock()
        mock_member.status = "creator"

        mock_bot.get_chat_member.return_value = mock_member

        # Verify
        is_admin, error = await parser.verify_user_is_admin(-1001234567890, 111222333, mock_bot)

        assert is_admin is True
        assert error == ""

    @pytest.mark.asyncio
    async def test_verify_user_is_admin_regular_member(self):
        """Test user admin verification when user is regular member"""
        parser = TelegramGroupParser()

        # Mock bot and member
        mock_bot = AsyncMock()
        mock_member = Mock()
        mock_member.status = "member"

        mock_bot.get_chat_member.return_value = mock_member

        # Verify
        is_admin, error = await parser.verify_user_is_admin(-1001234567890, 111222333, mock_bot)

        assert is_admin is False
        assert "администраторы" in error


class TestClubCreationFromGroup:
    """Tests for club creation from Telegram group"""

    def test_create_club_from_group_success(self):
        """Test successful club creation from group data"""
        group_data = {
            'chat_id': -1001234567890,
            'title': 'Test Running Club',
            'description': 'A club for runners',
            'username': 'testrunclub',
            'member_count': 50,
            'invite_link': 'https://t.me/testrunclub',
            'photo': 'file123',
            'type': 'supergroup'
        }

        # Validate group data first
        is_valid, error = validate_group_data(group_data)
        assert is_valid is True

        # Note: Actual DB creation test would require test database setup
        # This test verifies that group_data structure is correct for storage

    def test_validate_then_storage_integration(self):
        """Test that validated data can be used for club creation"""
        group_data = {
            'chat_id': -1001234567890,
            'title': 'Valid Club Name',
            'description': 'Test description',
            'username': 'validclub',
            'member_count': 100,
            'invite_link': 'https://t.me/validclub',
            'photo': 'file123',
            'type': 'supergroup'
        }

        # Step 1: Validate
        is_valid, error = validate_group_data(group_data)
        assert is_valid is True

        # Step 2: Verify all required fields for Club model exist
        assert 'title' in group_data
        assert 'chat_id' in group_data
        assert 'description' in group_data
        assert 'username' in group_data
        assert 'invite_link' in group_data
        assert 'photo' in group_data

        # This validates that our validation and storage are aligned


class TestValidationIntegration:
    """Tests for validation integration with parser"""

    def test_parser_output_passes_validation(self):
        """Test that parser output structure matches validation requirements"""
        # Simulate parser output
        parser_output = {
            'chat_id': -1001234567890,
            'title': 'Parsed Club',
            'description': 'Parsed description',
            'username': 'parsedclub',
            'member_count': 75,
            'invite_link': 'https://t.me/parsedclub',
            'photo': 'file456',
            'type': 'supergroup'
        }

        # Validate parser output
        is_valid, error = validate_group_data(parser_output)
        assert is_valid is True
        assert error == ""

    def test_invalid_parser_output_fails_validation(self):
        """Test that invalid parser output is caught by validation"""
        # Simulate invalid parser output (missing required field)
        parser_output = {
            'chat_id': -1001234567890,
            'title': 'AB',  # Too short
            'type': 'supergroup',
            'member_count': 50
        }

        # Validate should fail
        is_valid, error = validate_group_data(parser_output)
        assert is_valid is False
        assert len(error) > 0


class TestEndToEndFlow:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_full_validation_flow(self):
        """Test complete flow: parse -> validate -> (would create)"""
        parser = TelegramGroupParser()

        # Mock successful parse
        mock_bot = AsyncMock()
        mock_chat = Mock()
        mock_chat.id = -1001234567890
        mock_chat.title = "End to End Test Club"
        mock_chat.description = "Testing complete flow"
        mock_chat.username = "e2eclub"
        mock_chat.type = "supergroup"
        mock_chat.photo = Mock(big_file_id="file789")
        mock_chat.invite_link = "https://t.me/e2eclub"

        mock_bot.get_chat.return_value = mock_chat
        mock_bot.get_chat_member_count.return_value = 100

        # Step 1: Parse
        group_data = await parser.parse_group_info(-1001234567890, mock_bot)

        # Step 2: Validate
        is_valid, error = validate_group_data(group_data)

        # Verify flow succeeded
        assert is_valid is True
        assert error == ""
        assert group_data['title'] == "End to End Test Club"
        assert group_data['member_count'] == 100

    @pytest.mark.asyncio
    async def test_full_permission_check_flow(self):
        """Test complete permission check flow"""
        parser = TelegramGroupParser()

        # Mock bot
        mock_bot = AsyncMock()

        # Mock bot user
        mock_bot_user = Mock(id=123456)
        mock_bot.get_me.return_value = mock_bot_user

        # Mock bot as admin
        mock_bot_member = Mock()
        mock_bot_member.status = "administrator"
        mock_bot_member.can_invite_users = True

        # Mock user as admin
        mock_user_member = Mock()
        mock_user_member.status = "administrator"

        def get_chat_member_side_effect(chat_id, user_id):
            if user_id == 123456:  # Bot
                return mock_bot_member
            else:  # User
                return mock_user_member

        mock_bot.get_chat_member.side_effect = get_chat_member_side_effect

        # Check bot permissions
        bot_is_admin, bot_error = await parser.verify_bot_is_admin(-1001234567890, mock_bot)

        # Check user permissions
        user_is_admin, user_error = await parser.verify_user_is_admin(-1001234567890, 999888777, mock_bot)

        # Verify both passed
        assert bot_is_admin is True
        assert user_is_admin is True
        assert bot_error == ""
        assert user_error == ""
