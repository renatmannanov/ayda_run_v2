"""
Unit tests for TelegramGroupParser
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from bot.group_parser import TelegramGroupParser


class TestGroupParser:
    """Тесты парсера информации о группе"""

    @pytest.mark.asyncio
    async def test_parse_group_info_success(self):
        """Тест успешного парсинга информации о группе"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        # Mock chat object
        mock_chat = Mock()
        mock_chat.id = -1001234567890
        mock_chat.title = "Test Running Club"
        mock_chat.description = "Club for runners"
        mock_chat.username = "testrunclub"
        mock_chat.type = "supergroup"
        mock_chat.photo = Mock()
        mock_chat.photo.big_file_id = "photo_file_id_123"
        mock_chat.invite_link = None

        bot.get_chat = AsyncMock(return_value=mock_chat)
        bot.get_chat_member_count = AsyncMock(return_value=42)

        # Execute
        result = await parser.parse_group_info(-1001234567890, bot)

        # Assert
        assert result['chat_id'] == -1001234567890
        assert result['title'] == "Test Running Club"
        assert result['description'] == "Club for runners"
        assert result['username'] == "testrunclub"
        assert result['member_count'] == 42
        assert result['invite_link'] == "https://t.me/testrunclub"
        assert result['photo'] == "photo_file_id_123"
        assert result['type'] == "supergroup"

    @pytest.mark.asyncio
    async def test_get_group_photo_exists(self):
        """Тест получения аватара группы (аватар есть)"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_chat = Mock()
        mock_chat.photo = Mock()
        mock_chat.photo.big_file_id = "avatar_file_id_456"

        bot.get_chat = AsyncMock(return_value=mock_chat)

        result = await parser.get_group_photo(-1001234567890, bot)

        assert result == "avatar_file_id_456"

    @pytest.mark.asyncio
    async def test_get_group_photo_not_exists(self):
        """Тест получения аватара группы (аватара нет)"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_chat = Mock()
        mock_chat.photo = None

        bot.get_chat = AsyncMock(return_value=mock_chat)

        result = await parser.get_group_photo(-1001234567890, bot)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_invite_link_with_username(self):
        """Тест получения invite link для группы с username"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_chat = Mock()
        mock_chat.username = "mygroup"
        mock_chat.invite_link = None

        bot.get_chat = AsyncMock(return_value=mock_chat)

        result = await parser.get_invite_link(-1001234567890, bot)

        assert result == "https://t.me/mygroup"

    @pytest.mark.asyncio
    async def test_get_invite_link_with_existing_link(self):
        """Тест получения существующего invite link"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_chat = Mock()
        mock_chat.username = None
        mock_chat.invite_link = "https://t.me/+ABC123def"

        bot.get_chat = AsyncMock(return_value=mock_chat)

        result = await parser.get_invite_link(-1001234567890, bot)

        assert result == "https://t.me/+ABC123def"

    @pytest.mark.asyncio
    async def test_get_invite_link_create_new(self):
        """Тест создания нового invite link"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_chat = Mock()
        mock_chat.username = None
        mock_chat.invite_link = None

        bot.get_chat = AsyncMock(return_value=mock_chat)
        bot.export_chat_invite_link = AsyncMock(return_value="https://t.me/+NEW123abc")

        result = await parser.get_invite_link(-1001234567890, bot)

        assert result == "https://t.me/+NEW123abc"
        bot.export_chat_invite_link.assert_called_once_with(-1001234567890)

    @pytest.mark.asyncio
    async def test_verify_bot_is_admin_success(self):
        """Тест проверки прав бота - бот является админом"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_bot_user = Mock()
        mock_bot_user.id = 123456789

        mock_member = Mock()
        mock_member.status = "administrator"
        mock_member.can_invite_users = True

        bot.get_me = AsyncMock(return_value=mock_bot_user)
        bot.get_chat_member = AsyncMock(return_value=mock_member)

        is_admin, error_msg = await parser.verify_bot_is_admin(-1001234567890, bot)

        assert is_admin is True
        assert error_msg == ""

    @pytest.mark.asyncio
    async def test_verify_bot_is_admin_not_admin(self):
        """Тест проверки прав бота - бот не админ"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_bot_user = Mock()
        mock_bot_user.id = 123456789

        mock_member = Mock()
        mock_member.status = "member"

        bot.get_me = AsyncMock(return_value=mock_bot_user)
        bot.get_chat_member = AsyncMock(return_value=mock_member)

        is_admin, error_msg = await parser.verify_bot_is_admin(-1001234567890, bot)

        assert is_admin is False
        assert "не является администратором" in error_msg

    @pytest.mark.asyncio
    async def test_verify_bot_is_admin_no_invite_permission(self):
        """Тест проверки прав бота - нет права приглашать"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_bot_user = Mock()
        mock_bot_user.id = 123456789

        mock_member = Mock()
        mock_member.status = "administrator"
        mock_member.can_invite_users = False

        bot.get_me = AsyncMock(return_value=mock_bot_user)
        bot.get_chat_member = AsyncMock(return_value=mock_member)

        is_admin, error_msg = await parser.verify_bot_is_admin(-1001234567890, bot)

        assert is_admin is False
        assert "Приглашать пользователей" in error_msg

    @pytest.mark.asyncio
    async def test_verify_user_is_admin_success(self):
        """Тест проверки прав пользователя - пользователь админ"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_member = Mock()
        mock_member.status = "administrator"

        bot.get_chat_member = AsyncMock(return_value=mock_member)

        is_admin, error_msg = await parser.verify_user_is_admin(-1001234567890, 987654321, bot)

        assert is_admin is True
        assert error_msg == ""

    @pytest.mark.asyncio
    async def test_verify_user_is_admin_creator(self):
        """Тест проверки прав пользователя - пользователь создатель"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_member = Mock()
        mock_member.status = "creator"

        bot.get_chat_member = AsyncMock(return_value=mock_member)

        is_admin, error_msg = await parser.verify_user_is_admin(-1001234567890, 987654321, bot)

        assert is_admin is True
        assert error_msg == ""

    @pytest.mark.asyncio
    async def test_verify_user_is_admin_not_admin(self):
        """Тест проверки прав пользователя - пользователь не админ"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_member = Mock()
        mock_member.status = "member"

        bot.get_chat_member = AsyncMock(return_value=mock_member)

        is_admin, error_msg = await parser.verify_user_is_admin(-1001234567890, 987654321, bot)

        assert is_admin is False
        assert "администраторы" in error_msg

    @pytest.mark.asyncio
    async def test_get_user_status(self):
        """Тест получения статуса пользователя"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        mock_member = Mock()
        mock_member.status = "administrator"

        bot.get_chat_member = AsyncMock(return_value=mock_member)

        status = await parser.get_user_status(-1001234567890, 987654321, bot)

        assert status == "administrator"

    @pytest.mark.asyncio
    async def test_get_user_status_error(self):
        """Тест получения статуса пользователя при ошибке"""
        parser = TelegramGroupParser()
        bot = AsyncMock()

        bot.get_chat_member = AsyncMock(side_effect=Exception("Chat not found"))

        status = await parser.get_user_status(-1001234567890, 987654321, bot)

        assert status == "unknown"
