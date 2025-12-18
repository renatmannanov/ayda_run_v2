"""
Telegram Bot Messages

Provides message text templates and formatting functions.
"""

from typing import Dict, Any, List


def get_welcome_message(first_name: str) -> str:
    """
    Welcome message for new users with consent request.

    Args:
        first_name: User's first name

    Returns:
        Formatted welcome message
    """
    return f"""Привет, {first_name}! 👋

Ayda Run — это приложение для спортивных сообществ Алматы.

Здесь ты можешь:
🏃 Найти тренировки и пробежки
👥 Присоединиться к беговым клубам
📅 Записываться в один клик

Для регистрации я использую твои данные из Telegram: имя и @username.

Это нужно, чтобы организаторы видели кто записался на тренировку.

Всё ок?"""


def get_consent_declined_message() -> str:
    """Message when user declines consent."""
    return """Понял! Без проблем 😊

Если передумаешь — просто напиши /start

Всегда рады тебя видеть! 👋"""


def get_sports_selection_message() -> str:
    """Message for sports selection screen."""
    return """Чем занимаешься? 🤔

Выбери виды активностей, которые тебе интересны (можно несколько):"""


def get_role_selection_message() -> str:
    """Message for role selection screen."""
    return """Отлично! 💪

Кто ты?"""


def get_intro_message() -> str:
    """App introduction message."""
    return """📱 Как устроено приложение:

🏠 Главная — твои тренировки и открытые активности поблизости

👥 Клубы и группы — беговые сообщества, к которым можно присоединиться

👤 Профиль — твоя страница с историей тренировок

➕ Создать — можешь создать активность, группу или клуб

Готов начать?"""


def get_completion_message(first_name: str, username: str = None) -> str:
    """
    Onboarding completion message.

    Args:
        first_name: User's first name
        username: User's username (optional)

    Returns:
        Formatted completion message
    """
    username_text = f"(@{username})" if username else ""
    return f"""Готово! 🎉

Ты зарегистрирован как {first_name} {username_text}

Теперь открой приложение и найди ближайшую тренировку!"""


def get_returning_user_message(first_name: str) -> str:
    """
    Welcome back message for returning users.

    Args:
        first_name: User's first name

    Returns:
        Formatted welcome back message
    """
    return f"""С возвращением, {first_name}! 👋

Рад тебя снова видеть!"""


def format_club_invitation_message(first_name: str, club_data: Dict[str, Any]) -> str:
    """
    Format club invitation message for new users.

    Args:
        first_name: User's first name
        club_data: Dictionary with club data (from ClubStorage.get_club_preview)

    Returns:
        Formatted invitation message
    """
    return f"""Привет, {first_name}! 👋

Тебя пригласили в клуб:

┌────────────────────────────────────┐
│ 🏆 {club_data['name']}
│ {club_data['member_count']} участников · {club_data['groups_count']} групп
│
│ {club_data['description']}
└────────────────────────────────────┘

Ayda Run — это приложение для спортивных сообществ, где ты сможешь:
🏃 Видеть расписание тренировок
📅 Записываться в один клик
👥 Общаться с единомышленниками"""


def format_group_invitation_message(first_name: str, group_data: Dict[str, Any]) -> str:
    """
    Format group invitation message for new users.

    Args:
        first_name: User's first name
        group_data: Dictionary with group data (from GroupStorage.get_group_preview)

    Returns:
        Formatted invitation message
    """
    club_info = ""
    if not group_data['is_independent']:
        club_info = f"\n│ Часть клуба: 🏆 {group_data['club_name']}"

    return f"""Привет, {first_name}! 👋

Тебя пригласили в группу:

┌────────────────────────────────────┐
│ 👥 {group_data['name']}
│ {group_data['member_count']} участников{club_info}
│
│ {group_data['description']}
└────────────────────────────────────┘

Ayda Run — это приложение для спортивных сообществ, где ты сможешь:
🏃 Видеть расписание тренировок
📅 Записываться в один клик
👥 Общаться с единомышленниками"""


def format_existing_user_club_invitation(first_name: str, club_data: Dict[str, Any]) -> str:
    """
    Format club invitation message for existing users.

    Args:
        first_name: User's first name
        club_data: Dictionary with club data

    Returns:
        Formatted invitation message
    """
    return f"""С возвращением, {first_name}! 👋

Тебя пригласили в клуб:

┌────────────────────────────────────┐
│ 🏆 {club_data['name']}
│ {club_data['member_count']} участников · {club_data['groups_count']} групп
│
│ {club_data['description']}
└────────────────────────────────────┘

Присоединяешься?"""


def format_existing_user_group_invitation(first_name: str, group_data: Dict[str, Any]) -> str:
    """
    Format group invitation message for existing users.

    Args:
        first_name: User's first name
        group_data: Dictionary with group data

    Returns:
        Formatted invitation message
    """
    club_info = ""
    if not group_data['is_independent']:
        club_info = f"\n│ Часть клуба: 🏆 {group_data['club_name']}"

    return f"""С возвращением, {first_name}! 👋

Тебя пригласили в группу:

┌────────────────────────────────────┐
│ 👥 {group_data['name']}
│ {group_data['member_count']} участников{club_info}
│
│ {group_data['description']}
└────────────────────────────────────┘

Присоединяешься?"""


def get_club_not_found_message() -> str:
    """Message when club is not found."""
    return """❌ Упс! Не могу найти этот клуб.

Возможно, ссылка устарела или клуб был удалён.

Попробуй запросить новую ссылку у организатора."""


def get_group_not_found_message() -> str:
    """Message when group is not found."""
    return """❌ Упс! Не могу найти эту группу.

Возможно, ссылка устарела или группа была удалена.

Попробуй запросить новую ссылку у организатора."""


def get_already_member_message(entity_type: str = "клуба") -> str:
    """
    Message when user is already a member.

    Args:
        entity_type: "клуба" or "группы"

    Returns:
        Formatted message
    """
    return f"""👋 Ты уже участник этого {entity_type}!

Открой приложение, чтобы посмотреть расписание тренировок."""


def get_join_success_message(entity_name: str, entity_type: str = "клуба") -> str:
    """
    Success message after joining club/group.

    Args:
        entity_name: Name of club/group
        entity_type: "клуба" or "группы"

    Returns:
        Formatted success message
    """
    return f"""Добро пожаловать в {entity_name}! 🎉

Ты теперь участник {entity_type}.

Открой приложение, чтобы увидеть расписание тренировок и записаться."""


def get_invitation_declined_message() -> str:
    """Message when user declines invitation."""
    return """Хорошо! Ссылка будет работать, когда решишь присоединиться.

Или можешь посмотреть публичные тренировки в приложении 👇"""


def get_onboarding_cancelled_message() -> str:
    """Message when onboarding is cancelled or times out."""
    return """Онбординг отменён.

Напиши /start чтобы начать заново."""


# ============= ORGANIZER MESSAGES =============

def get_organizer_choice_message() -> str:
    """Message for organizer role selection."""
    return """Круто, что хочешь организовать спортивное сообщество! 💪

Что ты хочешь создать?"""


def get_club_creation_intro_message() -> str:
    """Introduction message for club creation."""
    return """🏆 Создание клуба

Клуб — это организация, которая объединяет несколько групп.

Например: Almaty Runners
├── Утренние пробежки
├── Вечерний бег
└── Выходные трейлы

⚠️ Сейчас создание клубов в бета-режиме.
Ты заполнишь форму, и мы свяжемся для настройки.

Обычно это занимает 1-2 дня."""


def get_group_creation_message() -> str:
    """Message about group creation in app."""
    return """👥 Создание группы

Группу можно создать прямо в приложении!

Открой Ayda Run → нажми "+" → выбери "Создать группу" """


def get_club_name_request_message() -> str:
    """Request club name."""
    return """Как называется твой клуб?

Напиши название:"""


def get_club_description_request_message(club_name: str) -> str:
    """
    Request club description.

    Args:
        club_name: Name of the club

    Returns:
        Formatted request message
    """
    return f"""👍 {club_name} — отличное название!

Теперь напиши краткое описание клуба (1-2 предложения):"""


def get_club_sports_request_message() -> str:
    """Request club sports selection."""
    return """Какие виды активностей у вас?

(выбери все подходящие)"""


def get_club_members_count_request_message() -> str:
    """Request club members count."""
    return """Сколько примерно участников в клубе?

Напиши число:"""


def get_club_groups_count_request_message() -> str:
    """Request club groups count."""
    return """Сколько групп внутри клуба?

Например, у вас могут быть разные группы по направлениям или уровню подготовки.

Напиши число (можно примерно):"""


def get_club_telegram_request_message() -> str:
    """Request Telegram chat connection."""
    return """Хочешь подключить Telegram чат?

Если добавишь нашего бота @ayda_run_v2_bot в вашу группу, мы сможем:

✨ Автоматически создать клуб с данными из вашего чата
📢 Отправлять уведомления о тренировках
👥 Синхронизировать участников
✅ Отмечать посещаемость

Это можно сделать сейчас или позже."""


def get_club_telegram_instructions_message() -> str:
    """Instructions for connecting Telegram chat."""
    return """Отлично! Вот что нужно сделать:

1. Добавь @ayda_run_v2_bot в вашу группу
2. Сделай бота администратором
3. Пришли сюда ссылку на группу
   (формат: https://t.me/... или @...)"""


def get_club_contact_request_message(username: str = None) -> str:
    """
    Request contact information.

    Args:
        username: User's Telegram username

    Returns:
        Formatted request message
    """
    telegram_info = f"@{username}" if username else "Telegram"
    return f"""Как с тобой лучше связаться?

Я напишу тебе в {telegram_info} или укажи другой способ:"""


def format_club_confirmation_message(form_data: Dict[str, Any]) -> str:
    """
    Format club request confirmation message.

    Args:
        form_data: Dictionary with club request data

    Returns:
        Formatted confirmation message
    """
    sports_list = ", ".join(form_data.get('sports', []))
    telegram_info = form_data.get('telegram_group_link', 'Не указано')
    contact = form_data.get('contact', 'Telegram')

    return f"""📋 Проверь заявку:

🏆 Клуб: {form_data['name']}
📝 Описание: {form_data.get('description', 'Не указано')}
🏃 Спорт: {sports_list if sports_list else 'Не указано'}
👥 Участников: ~{form_data.get('members_count', 'Не указано')}
📂 Групп: ~{form_data.get('groups_count', 'Не указано')}
💬 Telegram: {telegram_info}
👤 Контакт: {contact}

Всё верно?"""


def get_club_request_submitted_message() -> str:
    """Message after club request is submitted."""
    return """Заявка отправлена! 🎉

Я свяжусь с тобой в течение 1-2 дней для настройки клуба.

А пока можешь посмотреть как работает приложение:"""


def format_admin_club_request_notification(request_data: Dict[str, Any]) -> str:
    """
    Format admin notification about new club request.

    Args:
        request_data: Dictionary with club request data

    Returns:
        Formatted notification message
    """
    sports_list = ", ".join(request_data.get('sports', []))
    user_name = request_data.get('user_name', 'Unknown')
    username = request_data.get('username', '')
    username_text = f"@{username}" if username else "нет username"

    from datetime import datetime
    date_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    return f"""📥 НОВАЯ ЗАЯВКА НА КЛУБ

🏆 Название: {request_data['name']}
📝 Описание: {request_data.get('description', 'Не указано')}
🏃 Спорт: {sports_list if sports_list else 'Не указано'}
👥 Участников: ~{request_data.get('members_count', 'Не указано')}
📂 Групп: ~{request_data.get('groups_count', 'Не указано')}
💬 Telegram группа: {request_data.get('telegram_group_link', 'Не указано')}
👤 Заявитель: {user_name} ({username_text})
📅 Дата: {date_str}"""


def get_invalid_input_message(field_name: str) -> str:
    """
    Message for invalid input.

    Args:
        field_name: Name of the field

    Returns:
        Formatted error message
    """
    return f"""❌ Некорректный ввод для поля "{field_name}".

Попробуй ещё раз."""
