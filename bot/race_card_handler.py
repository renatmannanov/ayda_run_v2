"""
Race Card Handler for Telegram Bot

Implements ConversationHandler for /racecard command.
Generates social media cards from MyRace URLs.
"""

import logging
from io import BytesIO
from telegram import Update, InputMediaPhoto
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from telegram.constants import ParseMode

from analytics.race_cards.service import (
    get_race_card_service,
    RaceCardServiceError
)
from analytics.race_cards.parser import MyRaceParser

logger = logging.getLogger(__name__)

# Conversation states
STATE_WAITING_URL = 30

# Messages (Russian)
MESSAGES = {
    "start": (
        "🏃 <b>Генератор карточки результата</b>\n\n"
        "Отправь ссылку на свой результат с MyRace.\n\n"
        "Формат: <code>https://live.myrace.info/?f=...&amp;B=320</code>\n\n"
        "Где <b>B=</b> — твой номер участника.\n\n"
        "Для отмены напиши /cancel"
    ),
    "invalid_url": (
        "❌ <b>Неверный формат ссылки</b>\n\n"
        "Ссылка должна быть с сайта <b>live.myrace.info</b> и содержать номер участника (B=).\n\n"
        "Пример:\n"
        "<code>https://live.myrace.info/?f=bases/kz/2026/amangeldyrace2026/amrace2026.clax&amp;B=320</code>\n\n"
        "Попробуй ещё раз или напиши /cancel для отмены."
    ),
    "processing": "⏳ Загружаю данные и генерирую карточки...\n\nЭто может занять до 30 секунд.",
    "error": (
        "❌ <b>Не удалось сгенерировать карточки</b>\n\n"
        "Возможные причины:\n"
        "• Страница не загрузилась\n"
        "• Результат не найден по этому номеру\n"
        "• Сервис временно недоступен\n\n"
        "Попробуй ещё раз или обратись в поддержку @ayda_almaty"
    ),
    "success": (
        "✅ <b>Готово!</b>\n\n"
        "📸 <b>Первая картинка</b> — для одного поста (1080×1350)\n"
        "📑 <b>Следующие 3</b> — для карусели в Instagram\n\n"
        "Скачай и делись результатами в соцсетях! 🏆"
    ),
    "cancelled": "❌ Генерация карточки отменена.\n\nНапиши /racecard чтобы начать заново.",
}


async def start_racecard_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point for /racecard command.
    Asks user to send MyRace URL.
    """
    logger.info(f"User {update.effective_user.id} started /racecard")

    await update.message.reply_text(
        MESSAGES["start"],
        parse_mode=ParseMode.HTML
    )
    return STATE_WAITING_URL


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle URL input from user.
    Validates URL, parses data, generates cards, sends images.
    """
    url = update.message.text.strip()
    user_id = update.effective_user.id

    logger.info(f"User {user_id} sent URL: {url}")

    # Validate URL format
    is_valid, result = MyRaceParser.validate_url(url)
    if not is_valid:
        logger.warning(f"Invalid URL from user {user_id}: {result}")
        await update.message.reply_text(
            MESSAGES["invalid_url"],
            parse_mode=ParseMode.HTML
        )
        return STATE_WAITING_URL

    # Send processing message
    processing_msg = await update.message.reply_text(
        MESSAGES["processing"],
        parse_mode=ParseMode.HTML
    )

    try:
        # Get service and generate cards
        service = await get_race_card_service()
        output = await service.generate_from_url(url)

        # Delete processing message
        try:
            await processing_msg.delete()
        except Exception:
            pass  # Ignore if can't delete

        # Send single post card first
        await update.message.reply_photo(
            photo=BytesIO(output.single_post),
            caption="📸 Карточка для поста (1080×1350)"
        )

        # Send carousel as media group (album)
        media_group = []
        for i, slide in enumerate(output.carousel_slides):
            caption = "📑 Карусель для Instagram (3 слайда)" if i == 0 else None
            media_group.append(
                InputMediaPhoto(
                    media=BytesIO(slide),
                    caption=caption
                )
            )

        await update.message.reply_media_group(media=media_group)

        # Send success message
        await update.message.reply_text(
            MESSAGES["success"],
            parse_mode=ParseMode.HTML
        )

        logger.info(f"Successfully sent race cards to user {user_id}")
        return ConversationHandler.END

    except RaceCardServiceError as e:
        logger.error(f"Race card service error for user {user_id}: {e}")
        try:
            await processing_msg.edit_text(
                MESSAGES["error"],
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await update.message.reply_text(
                MESSAGES["error"],
                parse_mode=ParseMode.HTML
            )
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Unexpected error in race card handler for user {user_id}: {e}", exc_info=True)
        try:
            await processing_msg.edit_text(
                MESSAGES["error"],
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await update.message.reply_text(
                MESSAGES["error"],
                parse_mode=ParseMode.HTML
            )
        return ConversationHandler.END


async def cancel_racecard_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the race card flow."""
    logger.info(f"User {update.effective_user.id} cancelled /racecard")
    await update.message.reply_text(
        MESSAGES["cancelled"],
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END


async def timeout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle conversation timeout."""
    if update and update.effective_user:
        logger.info(f"Racecard conversation timeout for user {update.effective_user.id}")
    return ConversationHandler.END


# ConversationHandler for /racecard command
racecard_conv_handler = ConversationHandler(
    entry_points=[
        CommandHandler("racecard", start_racecard_flow)
    ],
    states={
        STATE_WAITING_URL: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url)
        ],
        ConversationHandler.TIMEOUT: [
            MessageHandler(filters.ALL, timeout_handler)
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel_racecard_flow)
    ],
    conversation_timeout=300,  # 5 minutes
)


def get_racecard_handler() -> ConversationHandler:
    """Get the race card conversation handler for registration."""
    return racecard_conv_handler
