"""
Локальный тест команды /create_club через polling

Запускает бота в режиме polling для тестирования команды /create_club
без необходимости настройки webhook.

Использование:
    python scripts/test_create_club_local.py

Остановка:
    Ctrl+C
"""

import asyncio
import sys
import os
import logging

# Добавить корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram.ext import Application
from config import settings
from bot.onboarding_handler import onboarding_conv_handler
from bot.invitation_handler import join_invitation_handlers
from bot.organizer_handler import organizer_conv_handler
from bot.group_club_creation_handler import group_club_creation_handler
from storage.db import init_db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("Тестирование команды /create_club через polling")
    print("="*60 + "\n")

    # Инициализация БД
    init_db()
    logger.info("Database initialized")

    # Создание бота
    app = Application.builder().token(settings.bot_token).build()

    # Регистрация handlers
    logger.info("Registering handlers...")
    app.add_handler(onboarding_conv_handler)

    for handler in join_invitation_handlers:
        app.add_handler(handler)

    app.add_handler(organizer_conv_handler)
    app.add_handler(group_club_creation_handler)

    logger.info("✅ All handlers registered")

    print("\n" + "-"*60)
    print("Бот запущен в режиме polling!")
    print("-"*60)
    print("\nТеперь в Telegram группе:")
    print("  1. Убедись, что бот добавлен в группу как администратор")
    print("  2. Напиши команду: /create_club")
    print("\nДля остановки нажми Ctrl+C")
    print("-"*60 + "\n")

    # Запуск polling
    try:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)

        # Бесконечный цикл
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\nОстановка бота...")

    finally:
        if app.updater.running:
            await app.updater.stop()
        if app.running:
            await app.stop()
        await app.shutdown()
        print("Бот остановлен.\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nПрограмма завершена.")
