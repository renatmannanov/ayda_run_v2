"""
Telegram Bot Validators

Provides validation functions for user input.
"""

import re
from typing import Tuple


def validate_club_name(name: str) -> Tuple[bool, str]:
    """
    Validate club name.

    Args:
        name: Club name to validate

    Returns:
        Tuple of (is_valid, error_message or cleaned_name)
    """
    if not name or not name.strip():
        return False, "Название не может быть пустым"

    cleaned = name.strip()

    if len(cleaned) < 3:
        return False, "Название слишком короткое (минимум 3 символа)"

    if len(cleaned) > 100:
        return False, "Название слишком длинное (максимум 100 символов)"

    return True, cleaned


def validate_description(description: str) -> Tuple[bool, str]:
    """
    Validate club/group description.

    Args:
        description: Description to validate

    Returns:
        Tuple of (is_valid, error_message or cleaned_description)
    """
    if not description or not description.strip():
        return False, "Описание не может быть пустым"

    cleaned = description.strip()

    if len(cleaned) < 10:
        return False, "Описание слишком короткое (минимум 10 символов)"

    if len(cleaned) > 500:
        return False, "Описание слишком длинное (максимум 500 символов)"

    return True, cleaned


def validate_members_count(count_str: str) -> Tuple[bool, int]:
    """
    Validate members count input.

    Args:
        count_str: String representation of member count

    Returns:
        Tuple of (is_valid, error_message or count_value)
    """
    try:
        count = int(count_str.strip())

        if count < 1:
            return False, "Количество участников должно быть больше 0"

        if count > 10000:
            return False, "Количество участников не может быть больше 10000"

        return True, count

    except ValueError:
        return False, "Пожалуйста, введи число"


def validate_groups_count(count_str: str) -> Tuple[bool, int]:
    """
    Validate groups count input.

    Args:
        count_str: String representation of groups count

    Returns:
        Tuple of (is_valid, error_message or count_value)
    """
    try:
        count = int(count_str.strip())

        if count < 1:
            return False, "Количество групп должно быть больше 0"

        if count > 100:
            return False, "Количество групп не может быть больше 100"

        return True, count

    except ValueError:
        return False, "Пожалуйста, введи число"


def is_valid_telegram_link(link: str) -> bool:
    """
    Check if string is a valid Telegram link or username.

    Args:
        link: Link or username to validate

    Returns:
        True if valid, False otherwise
    """
    if not link or not link.strip():
        return False

    cleaned = link.strip()

    # Check for t.me links
    if cleaned.startswith('http://') or cleaned.startswith('https://'):
        # Should be https://t.me/something or http://t.me/something
        pattern = r'^https?://t\.me/[\w\d_]+$'
        return bool(re.match(pattern, cleaned))

    # Check for @username format
    if cleaned.startswith('@'):
        # Should be @username (alphanumeric and underscore, 5-32 chars)
        pattern = r'^@[\w\d_]{5,32}$'
        return bool(re.match(pattern, cleaned))

    return False


def validate_telegram_link(link: str) -> Tuple[bool, str]:
    """
    Validate and clean Telegram link.

    Args:
        link: Telegram link or username

    Returns:
        Tuple of (is_valid, error_message or cleaned_link)
    """
    if not is_valid_telegram_link(link):
        return False, "Некорректная ссылка. Формат: https://t.me/... или @username"

    return True, link.strip()


def validate_contact(contact: str) -> Tuple[bool, str]:
    """
    Validate contact information.

    Args:
        contact: Contact string (phone, telegram username, etc)

    Returns:
        Tuple of (is_valid, error_message or cleaned_contact)
    """
    if not contact or not contact.strip():
        return False, "Контакт не может быть пустым"

    cleaned = contact.strip()

    if len(cleaned) < 3:
        return False, "Контакт слишком короткий"

    if len(cleaned) > 100:
        return False, "Контакт слишком длинный (максимум 100 символов)"

    return True, cleaned


def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """
    Validate phone number.

    Args:
        phone: Phone number string

    Returns:
        Tuple of (is_valid, error_message or cleaned_phone)
    """
    if not phone or not phone.strip():
        return False, "Номер телефона не может быть пустым"

    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)

    # Check if contains only digits and optionally starts with +
    if not re.match(r'^\+?\d{10,15}$', cleaned):
        return False, "Некорректный номер телефона. Используй формат: +7XXXXXXXXXX"

    return True, cleaned


def validate_group_data(group_data: dict) -> Tuple[bool, str]:
    """
    Validate Telegram group data before creating a club.

    Checks:
    - Title is not empty and not too short
    - Chat ID is valid
    - Chat type is group or supergroup
    - Member count is reasonable

    Args:
        group_data: Dictionary with group information from TelegramGroupParser

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check title exists
    if not group_data.get('title'):
        return False, "Название группы не найдено"

    # Check title length
    if len(group_data['title'].strip()) < 3:
        return False, "Название группы слишком короткое (минимум 3 символа)"

    if len(group_data['title'].strip()) > 255:
        return False, "Название группы слишком длинное (максимум 255 символов)"

    # Check chat type
    if group_data.get('type') not in ['group', 'supergroup']:
        return False, "Команда работает только в группах и супергруппах"

    # Check chat_id exists
    if not group_data.get('chat_id'):
        return False, "Не удалось определить ID группы"

    # Check member count is reasonable
    member_count = group_data.get('member_count', 0)
    if member_count < 2:
        return False, "В группе должно быть минимум 2 участника"

    if member_count > 200000:
        return False, "Слишком большая группа для создания клуба"

    return True, ""
