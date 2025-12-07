from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
import logging

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.
    
    This is the entry point for users when they first interact with your bot.
    
    TODO: Customize this message for your project.
    - Update the welcome text
    - Add project-specific instructions
    - Include setup steps if needed
    """
    try:
        user = update.effective_user
        
        # TODO: Replace this text with your project's welcome message
        text = (
            f"👋 Привет, {user.first_name}! Добро пожаловать в наш бот.\\n\\n"
            "<b>TODO: Customize this message</b>\\n"
            "1. Explain what your bot does\\n"
            "2. Provide setup instructions if needed\\n"
            "3. List available commands\\n\\n"
            "Начните использовать бот, отправив сообщение!"
        )
        
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        logging.error(f"Error in start command: {e}")
        await update.message.reply_text(
            "Привет! Произошла ошибка, но я работаю. Попробуйте снова."
        )
