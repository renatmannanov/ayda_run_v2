"""
Unit tests for bot validators

Tests validation functions for group data and other inputs.
"""

import pytest
from bot.validators import validate_group_data


class TestValidateGroupData:
    """Tests for validate_group_data function"""

    def test_valid_group_data(self):
        """Test validation with valid group data"""
        group_data = {
            'title': 'Test Running Club',
            'chat_id': -1001234567890,
            'type': 'supergroup',
            'member_count': 50,
            'description': 'Test description',
            'username': 'testclub'
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is True
        assert error == ""

    def test_missing_title(self):
        """Test validation fails when title is missing"""
        group_data = {
            'chat_id': -1001234567890,
            'type': 'supergroup',
            'member_count': 50
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is False
        assert "Название группы не найдено" in error

    def test_empty_title(self):
        """Test validation fails when title is empty"""
        group_data = {
            'title': '',
            'chat_id': -1001234567890,
            'type': 'supergroup',
            'member_count': 50
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is False
        assert "Название группы не найдено" in error

    def test_title_too_short(self):
        """Test validation fails when title is too short"""
        group_data = {
            'title': 'AB',
            'chat_id': -1001234567890,
            'type': 'supergroup',
            'member_count': 50
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is False
        assert "слишком короткое" in error

    def test_title_too_long(self):
        """Test validation fails when title is too long"""
        group_data = {
            'title': 'A' * 256,
            'chat_id': -1001234567890,
            'type': 'supergroup',
            'member_count': 50
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is False
        assert "слишком длинное" in error

    def test_invalid_chat_type(self):
        """Test validation fails for invalid chat type"""
        group_data = {
            'title': 'Test Club',
            'chat_id': -1001234567890,
            'type': 'private',
            'member_count': 50
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is False
        assert "группах и супергруппах" in error

    def test_missing_chat_id(self):
        """Test validation fails when chat_id is missing"""
        group_data = {
            'title': 'Test Club',
            'type': 'supergroup',
            'member_count': 50
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is False
        assert "ID группы" in error

    def test_member_count_too_low(self):
        """Test validation fails when member count is too low"""
        group_data = {
            'title': 'Test Club',
            'chat_id': -1001234567890,
            'type': 'supergroup',
            'member_count': 1
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is False
        assert "минимум 2 участника" in error

    def test_member_count_too_high(self):
        """Test validation fails when member count is too high"""
        group_data = {
            'title': 'Test Club',
            'chat_id': -1001234567890,
            'type': 'supergroup',
            'member_count': 300000
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is False
        assert "Слишком большая группа" in error

    def test_regular_group_type(self):
        """Test validation passes for regular group type"""
        group_data = {
            'title': 'Test Club',
            'chat_id': -1234567890,
            'type': 'group',
            'member_count': 50
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is True
        assert error == ""

    def test_edge_case_min_members(self):
        """Test validation with minimum valid member count"""
        group_data = {
            'title': 'Test Club',
            'chat_id': -1001234567890,
            'type': 'supergroup',
            'member_count': 2
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is True
        assert error == ""

    def test_edge_case_max_members(self):
        """Test validation with maximum valid member count"""
        group_data = {
            'title': 'Test Club',
            'chat_id': -1001234567890,
            'type': 'supergroup',
            'member_count': 200000
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is True
        assert error == ""

    def test_title_with_whitespace(self):
        """Test validation with title containing only whitespace"""
        group_data = {
            'title': '   ',
            'chat_id': -1001234567890,
            'type': 'supergroup',
            'member_count': 50
        }

        is_valid, error = validate_group_data(group_data)
        assert is_valid is False
        assert "слишком короткое" in error
