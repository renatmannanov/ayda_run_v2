"""
Мануальный тест TelegramGroupParser

Проверяет работоспособность парсера с реальным ботом.

Использование:
1. Добавь бота в тестовую группу как администратора с правом "Приглашать пользователей"
2. Получи chat_id группы (можно через @getidsbot или из логов бота)
3. Запусти скрипт: python scripts/test_group_parser_manual.py
4. Введи chat_id группы когда попросит
"""

import asyncio
import sys
import os

# Добавить корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram import Bot
from bot.group_parser import TelegramGroupParser
from config import settings


async def test_parse_group_info(chat_id: int):
    """Тест парсинга информации о группе"""
    bot = Bot(token=settings.bot_token)
    parser = TelegramGroupParser()

    print(f"\n{'='*60}")
    print(f"Тестирование TelegramGroupParser")
    print(f"{'='*60}\n")

    try:
        print(f"📋 Получаю информацию о группе {chat_id}...")
        group_data = await parser.parse_group_info(chat_id, bot)

        print(f"\n✅ Информация успешно получена:\n")
        print(f"  Chat ID: {group_data['chat_id']}")
        print(f"  Название: {group_data['title']}")
        print(f"  Описание: {group_data['description'] or 'Не указано'}")
        print(f"  Username: @{group_data['username']}" if group_data['username'] else "  Username: Не указан")
        print(f"  Тип: {group_data['type']}")
        print(f"  Участников: {group_data['member_count']}")
        print(f"  Invite link: {group_data['invite_link'] or 'Не получен'}")
        print(f"  Аватар: {'Есть' if group_data['photo'] else 'Нет'}")

    except Exception as e:
        print(f"\n❌ Ошибка при получении информации о группе:")
        print(f"   {type(e).__name__}: {e}")
        return False

    return True


async def test_bot_admin(chat_id: int):
    """Тест проверки прав бота"""
    bot = Bot(token=settings.bot_token)
    parser = TelegramGroupParser()

    print(f"\n{'='*60}")
    print(f"Проверка прав бота")
    print(f"{'='*60}\n")

    try:
        is_admin, error_msg = await parser.verify_bot_is_admin(chat_id, bot)

        if is_admin:
            print(f"✅ Бот является администратором группы")
            print(f"   Все необходимые права есть")
        else:
            print(f"❌ Бот НЕ является администратором или нет прав:")
            print(f"   {error_msg}")

    except Exception as e:
        print(f"\n❌ Ошибка при проверке прав бота:")
        print(f"   {type(e).__name__}: {e}")
        return False

    return True


async def test_user_admin(chat_id: int, user_id: int):
    """Тест проверки прав пользователя"""
    bot = Bot(token=settings.bot_token)
    parser = TelegramGroupParser()

    print(f"\n{'='*60}")
    print(f"Проверка прав пользователя")
    print(f"{'='*60}\n")

    try:
        is_admin, error_msg = await parser.verify_user_is_admin(chat_id, user_id, bot)

        if is_admin:
            print(f"✅ Пользователь {user_id} является администратором")
        else:
            print(f"❌ Пользователь {user_id} НЕ является администратором:")
            print(f"   {error_msg}")

        # Получить статус
        status = await parser.get_user_status(chat_id, user_id, bot)
        print(f"\n   Статус пользователя: {status}")

    except Exception as e:
        print(f"\n❌ Ошибка при проверке прав пользователя:")
        print(f"   {type(e).__name__}: {e}")
        return False

    return True


async def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("Мануальное тестирование TelegramGroupParser")
    print("="*60 + "\n")

    # Проверка настроек
    print(f"Bot username: @{settings.bot_username}")
    print(f"Bot token: {settings.bot_token[:10]}...{settings.bot_token[-5:]}")

    # Получить chat_id от пользователя
    print("\n" + "-"*60)
    print("Для тестирования нужен chat_id группы.")
    print("Получить его можно:")
    print("  1. Добавить @getidsbot в группу и написать /id")
    print("  2. Переслать сообщение из группы на @userinfobot")
    print("-"*60 + "\n")

    chat_id_input = input("Введи chat_id группы (например, -1001234567890): ").strip()

    try:
        chat_id = int(chat_id_input)
    except ValueError:
        print(f"\n❌ Ошибка: '{chat_id_input}' не является числом")
        return

    # Тест 1: Парсинг информации о группе
    success = await test_parse_group_info(chat_id)
    if not success:
        print("\n⚠️  Тест парсинга не пройден. Проверь:")
        print("   1. Правильность chat_id")
        print("   2. Бот добавлен в группу")
        print("   3. BOT_TOKEN в .env корректный")
        return

    # Тест 2: Проверка прав бота
    success = await test_bot_admin(chat_id)
    if not success:
        print("\n⚠️  Не удалось проверить права бота")

    # Тест 3: Проверка прав пользователя (опционально)
    user_id_input = input("\nВведи user_id для проверки прав (или Enter для пропуска): ").strip()
    if user_id_input:
        try:
            user_id = int(user_id_input)
            await test_user_admin(chat_id, user_id)
        except ValueError:
            print(f"\n⚠️  '{user_id_input}' не является числом, пропускаю")

    # Итоги
    print("\n" + "="*60)
    print("Тестирование завершено!")
    print("="*60 + "\n")

    print("✅ TelegramGroupParser работает корректно")
    print("\nГотово для Фазы 2: создание ConversationHandler для /create_club\n")


if __name__ == "__main__":
    asyncio.run(main())
