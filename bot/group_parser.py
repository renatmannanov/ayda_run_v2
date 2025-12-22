"""
Telegram Group Parser

Парсит информацию о Telegram группах для создания клубов.
Проверяет права бота и пользователей в группах.
"""

from typing import Optional, Dict, Any
from telegram import Bot
import logging

logger = logging.getLogger(__name__)


class TelegramGroupParser:
    """
    Парсер информации о Telegram группе

    Извлекает:
    - Базовую информацию (название, описание, username)
    - Статистику (количество участников)
    - Медиа (аватар группы)
    - Ссылки (invite link)

    Проверяет:
    - Права бота в группе
    - Права пользователя в группе
    """

    async def parse_group_info(self, chat_id: int, bot: Bot) -> Dict[str, Any]:
        """
        Получить информацию о группе

        Args:
            chat_id: Telegram chat ID группы
            bot: Telegram Bot instance

        Returns:
            {
                'chat_id': int,
                'title': str,
                'description': str,
                'username': str,  # @groupname (без @)
                'member_count': int,
                'invite_link': str,
                'photo': str,  # file_id аватара
                'type': str,  # 'group' или 'supergroup'
            }

        Raises:
            Exception: Если не удалось получить информацию о группе
        """
        try:
            # Получить информацию о чате
            chat = await bot.get_chat(chat_id)

            # Получить количество участников
            member_count = await bot.get_chat_member_count(chat_id)

            # Получить invite link (или создать если нет)
            invite_link = await self.get_invite_link(chat_id, bot)

            # Получить аватар
            photo_file_id = await self.get_group_photo(chat_id, bot)

            return {
                'chat_id': chat_id,
                'title': chat.title,
                'description': chat.description or '',
                'username': chat.username or '',  # Без @
                'member_count': member_count,
                'invite_link': invite_link,
                'photo': photo_file_id,
                'type': chat.type,  # 'group' или 'supergroup'
            }

        except Exception as e:
            logger.error(f"Error parsing group info for {chat_id}: {e}", exc_info=True)
            raise

    async def get_group_photo(self, chat_id: int, bot: Bot) -> Optional[str]:
        """
        Получить file_id аватара группы

        Args:
            chat_id: Telegram chat ID группы
            bot: Telegram Bot instance

        Returns:
            file_id фото или None если аватара нет
        """
        try:
            chat = await bot.get_chat(chat_id)
            if chat.photo:
                # Return file_id instead of file_path (URLs expire after 1 hour)
                return chat.photo.big_file_id
            return None
        except Exception as e:
            logger.error(f"Error getting group photo for chat {chat_id}: {e}")
            return None

    async def get_invite_link(self, chat_id: int, bot: Bot) -> Optional[str]:
        """
        Получить или создать invite link

        Сначала пробует получить существующий primary invite link.
        Если нет - создаёт новый.

        Args:
            chat_id: Telegram chat ID группы
            bot: Telegram Bot instance

        Returns:
            Invite link или None если не удалось получить
        """
        try:
            chat = await bot.get_chat(chat_id)

            # Если есть публичный username
            if chat.username:
                return f"https://t.me/{chat.username}"

            # Если есть invite_link
            if chat.invite_link:
                return chat.invite_link

            # Создать новый invite link
            invite_link = await bot.export_chat_invite_link(chat_id)
            return invite_link

        except Exception as e:
            logger.error(f"Error getting invite link for chat {chat_id}: {e}")
            return None

    async def verify_bot_is_admin(self, chat_id: int, bot: Bot) -> tuple[bool, str]:
        """
        Проверить, что бот является администратором группы

        Требуемые права:
        - can_invite_users (для создания invite links)

        Args:
            chat_id: Telegram chat ID группы
            bot: Telegram Bot instance

        Returns:
            (is_admin: bool, error_message: str)
        """
        try:
            bot_user = await bot.get_me()
            member = await bot.get_chat_member(chat_id, bot_user.id)

            if member.status not in ['administrator', 'creator']:
                return False, "Бот не является администратором группы"

            # Проверить права
            if not member.can_invite_users:
                return False, "У бота нет права 'Приглашать пользователей'"

            return True, ""

        except Exception as e:
            logger.error(f"Error verifying bot admin status in chat {chat_id}: {e}")
            return False, f"Ошибка проверки прав: {str(e)}"

    async def verify_user_is_admin(self, chat_id: int, user_id: int, bot: Bot) -> tuple[bool, str]:
        """
        Проверить, что пользователь является администратором или создателем

        Args:
            chat_id: Telegram chat ID группы
            user_id: Telegram user ID
            bot: Telegram Bot instance

        Returns:
            (is_admin: bool, error_message: str)
        """
        try:
            member = await bot.get_chat_member(chat_id, user_id)

            if member.status not in ['administrator', 'creator']:
                return False, "Только администраторы могут создавать клубы"

            return True, ""

        except Exception as e:
            logger.error(f"Error verifying user {user_id} admin status in chat {chat_id}: {e}")
            return False, f"Ошибка проверки прав: {str(e)}"

    async def get_user_status(self, chat_id: int, user_id: int, bot: Bot) -> str:
        """
        Получить статус пользователя в группе

        Args:
            chat_id: Telegram chat ID группы
            user_id: Telegram user ID
            bot: Telegram Bot instance

        Returns:
            'creator', 'administrator', 'member', 'restricted', 'left', 'kicked', или 'unknown'
        """
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            return member.status
        except Exception as e:
            logger.error(f"Error getting user {user_id} status in chat {chat_id}: {e}")
            return "unknown"
