"""
Telegram Bot Keyboards

Provides inline keyboard markup functions for bot interactions.
"""

from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def get_consent_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for consent to use Telegram data.

    Returns:
        InlineKeyboardMarkup with Yes/No buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Да, погнали!", callback_data="consent_yes"),
            InlineKeyboardButton("❌ Нет, не хочу", callback_data="consent_no"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_photo_visibility_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for selecting photo visibility during onboarding.

    Returns:
        InlineKeyboardMarkup with show/hide photo buttons
    """
    keyboard = [
        [InlineKeyboardButton("✅ Показывать фото", callback_data="photo_show")],
        [InlineKeyboardButton("👤 Скрыть (только инициалы)", callback_data="photo_hide")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_sports_selection_keyboard(selected: List[str] = None) -> InlineKeyboardMarkup:
    """
    Keyboard for selecting preferred sports (multi-select).

    Args:
        selected: List of currently selected sport IDs

    Returns:
        InlineKeyboardMarkup with sport buttons
    """
    if selected is None:
        selected = []

    # Sports: ID and Label (IDs match SportType enum names)
    sports = [
        ("RUNNING", "🏃 Бег"),
        ("TRAIL", "⛰️ Трейл"),
        ("HIKING", "🥾 Хайкинг"),
        ("CYCLING", "🚴 Вело"),
        ("YOGA", "🧘 Йога"),
        ("WORKOUT", "💪 Воркаут"),
    ]

    keyboard = []
    row = []
    for sport_id, sport_label in sports:
        checkbox = "☑️" if sport_id in selected else "☐"
        button = InlineKeyboardButton(
            f"{checkbox} {sport_label}",
            callback_data=f"sport_toggle_{sport_id}"
        )
        row.append(button)
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:  # Add remaining buttons if odd number
        keyboard.append(row)

    # Add Done and Skip buttons
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="sport_done")])
    keyboard.append([InlineKeyboardButton("⏭ Пропустить", callback_data="sport_skip")])

    return InlineKeyboardMarkup(keyboard)


def get_role_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for selecting user role (Participant or Organizer).

    Returns:
        InlineKeyboardMarkup with role buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("🏃 Хочу тренироваться", callback_data="role_participant"),
            InlineKeyboardButton("📋 Я организатор", callback_data="role_organizer"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_intro_done_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for app intro screen.

    Returns:
        InlineKeyboardMarkup with Ayda button
    """
    keyboard = [
        [InlineKeyboardButton("🏃 Айда!", callback_data="intro_done")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_webapp_button(url: str, text: str = "🚀 Открыть Ayda Run") -> InlineKeyboardMarkup:
    """
    Keyboard with WebApp button to open Mini App.

    Args:
        url: WebApp URL
        text: Button text

    Returns:
        InlineKeyboardMarkup with WebApp button
    """
    keyboard = [
        [InlineKeyboardButton(text, web_app=WebAppInfo(url=url))]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_club_invitation_keyboard(is_existing_user: bool = False) -> InlineKeyboardMarkup:
    """
    Keyboard for club invitation.

    Args:
        is_existing_user: Whether user already has account

    Returns:
        InlineKeyboardMarkup with appropriate buttons
    """
    if is_existing_user:
        keyboard = [
            [
                InlineKeyboardButton("✅ Вступить", callback_data="club_join_yes"),
                InlineKeyboardButton("❌ Не сейчас", callback_data="club_join_no"),
            ]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("▶️ Далее", callback_data="invitation_continue")]
        ]
    return InlineKeyboardMarkup(keyboard)


def get_group_invitation_keyboard(is_existing_user: bool = False) -> InlineKeyboardMarkup:
    """
    Keyboard for group invitation.

    Args:
        is_existing_user: Whether user already has account

    Returns:
        InlineKeyboardMarkup with appropriate buttons
    """
    if is_existing_user:
        keyboard = [
            [
                InlineKeyboardButton("✅ Вступить", callback_data="group_join_yes"),
                InlineKeyboardButton("❌ Не сейчас", callback_data="group_join_no"),
            ]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("▶️ Далее", callback_data="invitation_continue")]
        ]
    return InlineKeyboardMarkup(keyboard)


def get_org_type_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for organizer to choose between club and group.

    Returns:
        InlineKeyboardMarkup with club/group options
    """
    keyboard = [
        [InlineKeyboardButton("🏆 Клуб", callback_data="org_club")],
        [InlineKeyboardButton("👥 Группа", callback_data="org_group")],
        [InlineKeyboardButton("← Назад", callback_data="org_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_club_form_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for club form confirmation.

    Returns:
        InlineKeyboardMarkup with confirm button
    """
    keyboard = [
        [InlineKeyboardButton("✅ Отправить заявку", callback_data="club_confirm_submit")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_club_telegram_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for Telegram group connection option.

    Returns:
        InlineKeyboardMarkup with connect/skip buttons
    """
    keyboard = [
        [InlineKeyboardButton("🔗 Хочу подключить чат", callback_data="club_telegram_yes")],
        [InlineKeyboardButton("⏭ Пока пропустить", callback_data="club_telegram_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_club_contact_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for contact method selection.

    Returns:
        InlineKeyboardMarkup with contact options
    """
    keyboard = [
        [InlineKeyboardButton("✅ Пиши в Telegram", callback_data="club_contact_telegram")],
        [InlineKeyboardButton("📱 Указать телефон/WhatsApp", callback_data="club_contact_phone")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_approval_keyboard(request_id: str) -> InlineKeyboardMarkup:
    """
    Admin keyboard for approving/rejecting club requests.

    Args:
        request_id: ClubRequest UUID

    Returns:
        InlineKeyboardMarkup with approve/reject buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_club_{request_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_club_{request_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_declined_invitation_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard when user declines invitation.

    Returns:
        InlineKeyboardMarkup with explore activities button
    """
    keyboard = [
        [InlineKeyboardButton("🔍 Посмотреть тренировки", callback_data="explore_activities")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_club_form_start_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard to start filling club creation form.

    Returns:
        InlineKeyboardMarkup with start/back buttons
    """
    keyboard = [
        [InlineKeyboardButton("📝 Заполнить заявку", callback_data="form_start")],
        [InlineKeyboardButton("← Назад", callback_data="form_back")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_telegram_group_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for Telegram group connection option.

    Returns:
        InlineKeyboardMarkup with connect/skip buttons
    """
    keyboard = [
        [InlineKeyboardButton("🔗 Хочу подключить чат", callback_data="telegram_connect")],
        [InlineKeyboardButton("⏭ Пока пропустить", callback_data="telegram_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_contact_method_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for contact method selection.

    Returns:
        InlineKeyboardMarkup with contact options
    """
    keyboard = [
        [InlineKeyboardButton("✅ Пиши в Telegram", callback_data="contact_telegram")],
        [InlineKeyboardButton("📱 Указать телефон/WhatsApp", callback_data="contact_phone")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_club_request_summary_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for club request summary confirmation.

    Returns:
        InlineKeyboardMarkup with submit button
    """
    keyboard = [
        [InlineKeyboardButton("✅ Отправить заявку", callback_data="request_submit")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_join_request_keyboard(request_id: str, entity_type: str) -> InlineKeyboardMarkup:
    """
    Keyboard for organizer to approve/reject join requests.

    Args:
        request_id: JoinRequest UUID
        entity_type: "club", "group", or "activity"

    Returns:
        InlineKeyboardMarkup with approve/reject buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve_join_{entity_type}_{request_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_join_{entity_type}_{request_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_club_access_keyboard() -> InlineKeyboardMarkup:
    """
    Keyboard for selecting club access type during creation.

    Returns:
        InlineKeyboardMarkup with open/closed access buttons
    """
    keyboard = [
        [InlineKeyboardButton("🌍 Открыто для всех", callback_data="access_open")],
        [InlineKeyboardButton("🔒 Требуется одобрение", callback_data="access_closed")],
    ]
    return InlineKeyboardMarkup(keyboard)
