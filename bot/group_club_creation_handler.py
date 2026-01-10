"""
Group Club Creation Handler

Обрабатывает создание клубов из Telegram групп через команду /create_club.
Реализует ConversationHandler с проверками прав и пошаговым созданием клуба.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from bot.group_parser import TelegramGroupParser
from bot.validators import validate_group_data
from storage.user_storage import UserStorage
from storage.club_storage import ClubStorage
from storage.membership_storage import MembershipStorage
from storage.db import UserRole, SessionLocal
from config import settings
from bot.keyboards import get_sports_selection_keyboard, get_club_access_keyboard, get_webapp_button
from bot.messages import get_club_access_prompt
from permissions import check_club_creation_limit

logger = logging.getLogger(__name__)

# Conversation states
CONFIRMING_CLUB_CREATION = 1
SELECTING_SPORTS = 2
SELECTING_ACCESS = 3


# Custom exceptions
class GroupIntegrationError(Exception):
    """Базовая ошибка интеграции с группой"""
    pass


class BotNotAdminError(GroupIntegrationError):
    """Бот не является администратором"""
    pass


class UserNotAdminError(GroupIntegrationError):
    """Пользователь не является администратором"""
    pass


class GroupAlreadyLinkedError(GroupIntegrationError):
    """Группа уже связана с клубом"""
    pass


class NotInGroupError(GroupIntegrationError):
    """Команда вызвана не в группе"""
    pass


async def create_club_from_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handler для команды /create_club в группе

    Flow:
    1. Проверить, что команда вызвана в группе (не в ЛС)
    2. Проверить, что пользователь - админ/создатель группы
    3. Проверить, что бот - админ группы
    4. Проверить, что группа еще не связана с клубом
    5. Спарсить информацию о группе
    6. Показать превью клуба пользователю
    7. Запросить подтверждение
    8. При подтверждении -> выбор спортов -> создание клуба
    """
    try:
        message = update.message
        user = message.from_user
        chat = message.chat

        # 1. Проверка, что команда в группе
        if chat.type not in ['group', 'supergroup']:
            await message.reply_text(
                "ℹ️ Эта команда работает только в группах\n\n"
                "Добавьте меня в группу и вызовите /create_club там."
            )
            return ConversationHandler.END

        parser = TelegramGroupParser()

        # 2. Проверка прав пользователя
        is_user_admin, error_msg = await parser.verify_user_is_admin(
            chat.id, user.id, context.bot
        )
        if not is_user_admin:
            await message.reply_text(
                f"❌ {error_msg}\n\n"
                "Только администраторы и создатель группы могут создавать клубы."
            )
            return ConversationHandler.END

        # 2.1 Проверка лимита клубов пользователя
        with UserStorage() as user_storage:
            db_user = user_storage.get_user_by_telegram_id(user.id)
            if db_user:
                db = SessionLocal()
                try:
                    can_create, current, max_limit = check_club_creation_limit(db, db_user.id)
                    if not can_create:
                        await message.reply_text(
                            f"❌ Достигнут лимит клубов ({current}/{max_limit})\n\n"
                            "Вы уже создали максимальное количество клубов.\n"
                            "Удалите один из существующих клубов, чтобы создать новый."
                        )
                        return ConversationHandler.END
                finally:
                    db.close()

        # 3. Проверка прав бота
        is_bot_admin, error_msg = await parser.verify_bot_is_admin(
            chat.id, context.bot
        )
        if not is_bot_admin:
            await message.reply_text(
                f"❌ {error_msg}\n\n"
                "Чтобы создать клуб, добавьте меня как администратора с правами:\n"
                "▪️ Приглашать пользователей\n"
                "▪️ Читать сообщения"
            )
            return ConversationHandler.END

        # 4. Проверка, что группа не связана с клубом
        with ClubStorage() as club_storage:
            existing_club = club_storage.get_club_by_telegram_chat_id(chat.id)
            if existing_club:
                # Генерация deep link
                club_link = f"https://t.me/{settings.bot_username}?start=club_{existing_club.id}"

                await message.reply_text(
                    f"❌ Группа уже связана с клубом \"{existing_club.name}\"\n\n"
                    f"🔗 Перейти в клуб: {club_link}"
                )
                return ConversationHandler.END

        # 5. Парсинг информации о группе
        try:
            group_data = await parser.parse_group_info(chat.id, context.bot)
        except Exception as e:
            logger.error(f"Error parsing group {chat.id}: {e}", exc_info=True)
            await message.reply_text(
                "⚠️ Не удалось получить полную информацию о группе\n\n"
                "Убедитесь, что:\n"
                "▪️ Группа является супергруппой\n"
                "▪️ У бота есть необходимые права"
            )
            return ConversationHandler.END

        # 6. Валидация данных группы
        is_valid, error_message = validate_group_data(group_data)
        if not is_valid:
            logger.warning(f"Group data validation failed for {chat.id}: {error_message}")
            await message.reply_text(
                f"❌ Невозможно создать клуб:\n\n{error_message}\n\n"
                "Проверьте настройки группы и попробуйте снова."
            )
            return ConversationHandler.END

        # Сохранить данные в context
        context.user_data['group_data'] = group_data
        context.user_data['creator_telegram_id'] = user.id

        # 7. Показать preview
        return await show_club_preview(update, context, group_data)

    except Exception as e:
        logger.error(f"Error in create_club_from_group: {e}", exc_info=True)
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте позже."
        )
        return ConversationHandler.END


async def show_club_preview(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    group_data: dict
) -> int:
    """
    Показать превью будущего клуба на основе данных группы
    """
    message_text = (
        f"📋 Создание клуба на основе группы \"{group_data['title']}\"\n\n"
        f"Я нашел следующую информацию:\n"
        f"▪️ Название: {group_data['title']}\n"
        f"▪️ Описание: {group_data['description'] or 'Не указано'}\n"
        f"▪️ Участников: {group_data['member_count']}\n"
    )

    if group_data['username']:
        message_text += f"▪️ Группа: @{group_data['username']}\n"

    message_text += "\nХотите создать клуб с этими данными?"

    keyboard = [
        [
            InlineKeyboardButton("✅ Создать", callback_data="group_club_confirm"),
            InlineKeyboardButton("❌ Отменить", callback_data="group_club_cancel")
        ]
    ]

    await update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    return CONFIRMING_CLUB_CREATION


async def handle_club_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработка подтверждения создания клуба
    """
    query = update.callback_query
    await query.answer()

    if query.data == "group_club_cancel":
        await query.edit_message_text("❌ Создание клуба отменено")
        return ConversationHandler.END

    # Перейти к выбору спортов
    context.user_data['selected_sports'] = []

    await query.edit_message_text(
        "Выберите виды спорта для клуба:\n\n"
        "(Можно выбрать несколько)",
        reply_markup=get_sports_selection_keyboard([])
    )

    return SELECTING_SPORTS


async def handle_sports_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработка выбора спортов
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "sport_done":
        # Завершить выбор спортов
        selected = context.user_data.get('selected_sports', [])

        if not selected:
            await query.answer("Выберите хотя бы один вид спорта", show_alert=True)
            return SELECTING_SPORTS

        # Перейти к выбору доступа
        await query.edit_message_text(
            get_club_access_prompt(),
            reply_markup=get_club_access_keyboard()
        )
        return SELECTING_ACCESS

    if callback_data == "sport_skip":
        # Пропустить выбор спортов
        context.user_data['selected_sports'] = []
        # Перейти к выбору доступа
        await query.edit_message_text(
            get_club_access_prompt(),
            reply_markup=get_club_access_keyboard()
        )
        return SELECTING_ACCESS

    # Добавить/удалить спорт
    if callback_data.startswith("sport_toggle_"):
        sport = callback_data.replace("sport_toggle_", "")
        selected = context.user_data.get('selected_sports', [])

        if sport in selected:
            selected.remove(sport)
        else:
            selected.append(sport)

        context.user_data['selected_sports'] = selected

        # Обновить клавиатуру
        try:
            await query.edit_message_reply_markup(
                reply_markup=get_sports_selection_keyboard(selected)
            )
        except Exception as e:
            # Игнорировать ошибку "Message is not modified"
            logger.debug(f"Failed to update keyboard: {e}")
            pass

    return SELECTING_SPORTS


async def handle_access_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработка выбора типа доступа (открыт/закрыт)
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    # Determine is_open value
    is_open = callback_data == "access_open"
    context.user_data['is_open'] = is_open

    logger.info(f"User {query.from_user.id} set club is_open={is_open}")

    # Создать клуб
    return await finalize_club_creation(update, context)


async def finalize_club_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Финализация - создание клуба в БД
    """
    query = update.callback_query
    await query.answer()

    group_data = context.user_data.get('group_data')
    selected_sports = context.user_data.get('selected_sports', [])
    is_open = context.user_data.get('is_open', True)
    creator_telegram_id = context.user_data.get('creator_telegram_id')
    chat_id = group_data['chat_id']

    try:
        # Получить или создать пользователя
        with UserStorage() as user_storage:
            user = user_storage.get_user_by_telegram_id(creator_telegram_id)
            if not user:
                # Создать пользователя (не должно произойти, но на всякий случай)
                telegram_user = query.from_user
                user = user_storage.get_or_create_user(
                    telegram_id=telegram_user.id,
                    username=telegram_user.username,
                    first_name=telegram_user.first_name,
                    last_name=telegram_user.last_name
                )

        # Создать клуб
        with ClubStorage() as club_storage:
            club = club_storage.create_club_from_telegram_group(
                creator_id=user.id,
                group_data=group_data,
                sports=selected_sports,
                is_open=is_open
            )

        # Добавить создателя как ORGANIZER
        with MembershipStorage() as membership_storage:
            membership_storage.add_member_to_club(
                user_id=user.id,
                club_id=club.id,
                role=UserRole.ORGANIZER
            )

        logger.info(f"Club {club.id} created from group {chat_id}")

        # Phase 6: Get member count and import admins
        try:
            # 1. Get current member count from Telegram (minus 1 for the bot itself)
            tg_count = await context.bot.get_chat_member_count(chat_id)
            member_count = max(0, tg_count - 1)  # Exclude bot from count

            # 2. Save member count to club
            with ClubStorage() as cs:
                cs.update_telegram_member_count(club.id, member_count)

            # 3. Import group admins
            from bot.member_sync_handler import import_group_admins
            imported_count = await import_group_admins(context.bot, chat_id, club.id)

            logger.info(f"Club {club.id}: {member_count} members in TG, {imported_count} admins imported")
        except Exception as e:
            logger.error(f"Error during member sync setup: {e}")
            member_count = group_data.get('member_count', 0)
            imported_count = 0

        # Отправить уведомления
        await send_club_created_notifications(
            update, context, club, chat_id, member_count, imported_count
        )

        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error creating club: {e}", exc_info=True)
        await query.edit_message_text(
            "Произошла ошибка при создании клуба. Попробуйте позже."
        )
        return ConversationHandler.END


async def send_club_created_notifications(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    club,
    group_chat_id: int,
    member_count: int = 0,
    imported_count: int = 0
):
    """
    Отправить уведомления о создании клуба с информацией о синхронизации
    """
    query = update.callback_query

    # Уведомление в группу с кнопкой регистрации
    bot_link = f"https://t.me/{settings.bot_username}?start=club_{club.id}"
    join_link = f"https://t.me/{settings.bot_username}?start=join_{group_chat_id}"
    webapp_url = f"{settings.app_url}?startapp=club_{club.id}" if settings.app_url else bot_link

    remaining = max(0, member_count - imported_count)

    group_message = (
        f"🎉 Клуб \"{club.name}\" создан в Ayda Run!\n\n"
        f"👥 Всего в группе: {member_count}\n"
        f"✅ Организаторов добавлено: {imported_count}\n"
        f"⏳ Осталось зарегистрировать: {remaining}\n\n"
        f"Нажмите кнопку ниже, чтобы зарегистрироваться в клубе и получить доступ к:\n"
        f"▪️ Календарю тренировок\n"
        f"▪️ Статистике активностей\n"
        f"▪️ Записи на мероприятия"
    )

    # В группу отправляем кнопку регистрации (deep link)
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    group_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏃 Зарегистрироваться в Ayda Run", url=join_link)]
    ])

    await context.bot.send_message(
        chat_id=group_chat_id,
        text=group_message,
        reply_markup=group_keyboard
    )

    # Уведомление организатору в ЛС
    organizer_message = (
        f"✅ Поздравляем! Клуб \"{club.name}\" создан.\n\n"
        f"📊 Статус синхронизации:\n"
        f"▪️ В Telegram группе: {member_count} участников\n"
        f"▪️ Организаторов добавлено: {imported_count}\n"
        f"▪️ Ожидают регистрации: {remaining}\n\n"
        f"Участники группы могут зарегистрироваться двумя способами:\n"
        f"1️⃣ Нажать кнопку в группе\n"
        f"2️⃣ Автоматически при написании сообщений\n\n"
        f"Используйте команду /sync в группе для проверки статуса."
    )

    await query.edit_message_text(organizer_message)

    # WebApp кнопку в ЛС можно отправить
    if settings.app_url:
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text="Откройте приложение для управления клубом:",
            reply_markup=get_webapp_button(webapp_url, f"🚀 Управление клубом")
        )


async def cancel_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена создания клуба"""
    await update.message.reply_text("❌ Создание клуба отменено")
    return ConversationHandler.END


# ConversationHandler
group_club_creation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("create_club", create_club_from_group)
    ],
    states={
        CONFIRMING_CLUB_CREATION: [
            CallbackQueryHandler(handle_club_confirmation, pattern="^group_club_")
        ],
        SELECTING_SPORTS: [
            CallbackQueryHandler(handle_sports_selection, pattern="^sport_")
        ],
        SELECTING_ACCESS: [
            CallbackQueryHandler(handle_access_selection, pattern="^access_")
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_creation)
    ],
    conversation_timeout=600,  # 10 минут
    per_chat=False,  # Разные разговоры для разных чатов
    per_user=True,   # Но один разговор на пользователя
)
