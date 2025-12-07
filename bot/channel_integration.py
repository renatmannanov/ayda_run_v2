"""
Example: Channel Integration Handler

This module demonstrates a well-structured Telegram bot handler for channel integration.
It shows best practices for:
- Error handling and logging
- Data persistence (JSON files)
- Update propagation (channel → user)
- Message editing sync

Use this as a reference for implementing your own handlers.
"""

import json
import os
import logging
from typing import Dict, Optional
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from .utils import get_user_data

# Configuration files for channel-to-user mapping
CHANNEL_MAP_FILE = 'channel_map.json'
CHANNEL_MSG_MAP_FILE = 'channel_messages.json'

# ============================================================================
# Persistence Layer - JSON-based storage for channel mappings
# ============================================================================

def load_channel_mapping() -> Dict[str, int]:
    """
    Load channel-to-user mappings from persistent storage.
    
    Returns:
        Dictionary mapping channel_id (str) to user_id (int)
    """
    if not os.path.exists(CHANNEL_MAP_FILE):
        return {}
    try:
        with open(CHANNEL_MAP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Failed to parse {CHANNEL_MAP_FILE}")
        return {}

def save_channel_mapping(channel_id: int, user_id: int):
    """
    Save a channel-to-user mapping.
    
    Args:
        channel_id: Telegram channel ID
        user_id: Telegram user ID who owns the channel
    """
    mapping = load_channel_mapping()
    mapping[str(channel_id)] = user_id
    with open(CHANNEL_MAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=4)
    logging.info(f"Saved channel mapping: {channel_id} → user {user_id}")

def get_user_for_channel(channel_id: int) -> Optional[int]:
    """
    Get the user ID associated with a channel.
    
    Args:
        channel_id: Telegram channel ID
        
    Returns:
        User ID if found, None otherwise
    """
    mapping = load_channel_mapping()
    return mapping.get(str(channel_id))

def load_message_mapping() -> Dict[str, int]:
    """
    Load channel message-to-cloned message mappings.
    
    This tracks which channel messages were copied to which user messages,
    enabling us to sync edits.
    
    Returns:
        Dictionary mapping "channel_id:post_id" to cloned_message_id
    """
    if not os.path.exists(CHANNEL_MSG_MAP_FILE):
        return {}
    try:
        with open(CHANNEL_MSG_MAP_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Failed to parse {CHANNEL_MSG_MAP_FILE}")
        return {}

def save_message_mapping(channel_id: int, post_id: int, cloned_id: int):
    """
    Save a mapping between channel post and cloned user message.
    
    Args:
        channel_id: Channel where post originated
        post_id: Message ID in the channel
        cloned_id: Message ID of the copy in user's chat
    """
    mapping = load_message_mapping()
    key = f"{channel_id}:{post_id}"
    mapping[key] = cloned_id
    with open(CHANNEL_MSG_MAP_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=4)

def get_cloned_message_id(channel_id: int, post_id: int) -> Optional[int]:
    """
    Get the cloned message ID for a channel post.
    
    Args:
        channel_id: Channel ID
        post_id: Original post ID in channel
        
    Returns:
        Cloned message ID in user chat, or None
    """
    mapping = load_message_mapping()
    key = f"{channel_id}:{post_id}"
    return mapping.get(key)

# ============================================================================
# Command Handlers
# ============================================================================

async def link_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /link_channel command.
    
    User must reply to a forwarded message from the channel they want to link.
    This creates a mapping between the channel and the user.
    
    Flow:
        1. User forwards message from channel to bot
        2. User replies with /link_channel
        3. Bot extracts channel ID and saves mapping
        4. All future posts from that channel are saved for this user
    """
    user_id = update.effective_user.id
    message = update.message
    
    # Validate: command must be a reply
    if not message.reply_to_message:
        await message.reply_text("⚠️ Ответьте этой командой на пересланное сообщение из канала.")
        return

    reply = message.reply_to_message
    
    # Validate: must be forwarded from a channel
    if not reply.forward_origin or reply.forward_origin.type != 'channel':
        await message.reply_text("⚠️ Это сообщение не похоже на пересылку из канала.")
        return

    # Extract channel information
    channel_id = reply.forward_origin.chat.id
    channel_title = reply.forward_origin.chat.title
    
    # Save mapping
    save_channel_mapping(channel_id, user_id)
    
    await message.reply_text(
        f"✅ **Канал подключен!**\\n\\n"
        f"Канал: `{channel_title}` (ID: `{channel_id}`)\\n"
        f"Теперь сообщения из этого канала будут сохраняться.",
        parse_mode=ParseMode.MARKDOWN
    )

# ============================================================================
# Channel Post Handlers
# ============================================================================

async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle new posts in linked channels.
    
    Flow:
        1. Receive channel post
        2. Check if channel is linked to a user
        3. Extract content and metadata
        4. Save to storage (TODO: implement your storage logic)
        5. Clone message to user's chat for convenience
        6. Track the cloned message for future edits
    
    TODO: Customize the note_data structure for your project
    TODO: Implement your storage logic (replace context.bot_data['storage'])
    """
    logging.info(f"Received channel post update: {update}")
    
    if not update.channel_post:
        logging.info("Update is not a channel_post")
        return

    channel_id = update.channel_post.chat.id
    logging.info(f"Processing post from channel {channel_id}")
    
    # Check if this channel is linked to a user
    user_id = get_user_for_channel(channel_id)
    logging.info(f"Mapped user_id: {user_id}")
    
    if not user_id:
        # Channel not linked to any user, ignore
        return

    # TODO: Replace this with your user data retrieval logic
    # user_config = get_user_data(user_id)
    # if not user_config:
    #     logging.warning(f"User {user_id} has no configuration.")
    #     return

    post = update.channel_post
    content = post.text or post.caption or ""
    
    # Example: extract hashtags
    tags = [word for word in content.split() if word.startswith('#')]
    
    # Construct data object (customize this for your project)
    note_data = {
        'message_id': post.message_id,
        'content': content,
        'tags': tags,
        'message_type': 'channel_post',
        'source_chat_id': channel_id,
        'source_chat_link': _build_channel_link(post),
        'telegram_username': post.chat.username or post.chat.title
    }
    
    # TODO: Implement your storage logic here
    # Example:
    # storage = context.bot_data['storage']
    # try:
    #     await storage.save_data(user_id, note_data)
    #     logging.info(f"Saved channel post {post.message_id}")
    # except Exception as e:
    #     logging.error(f"Error saving channel post: {e}")
    
    # Clone message to user's chat
    try:
        cloned_msg = await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=channel_id,
            message_id=post.message_id
        )
        # Track this mapping for future edits
        save_message_mapping(channel_id, post.message_id, cloned_msg.message_id)
        logging.info(f"Cloned message {post.message_id} to user {user_id}")
        
    except Exception as e:
        logging.error(f"Error copying message to user {user_id}: {e}")

async def edited_channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle edited posts in linked channels.
    
    When a channel post is edited, we need to:
        1. Update the stored data
        2. Update the cloned message in user's chat
    
    This keeps everything in sync.
    """
    if not update.edited_channel_post:
        return

    post = update.edited_channel_post
    channel_id = post.chat.id
    user_id = get_user_for_channel(channel_id)
    
    if not user_id:
        return

    new_content = post.text or post.caption or ""
    new_tags = [word for word in new_content.split() if word.startswith('#')]
    
    # TODO: Update your storage
    # storage = context.bot_data['storage']
    # try:
    #     await storage.update_data(user_id, post.message_id, {
    #         'content': new_content,
    #         'tags': new_tags
    #     })
    #     logging.info(f"Updated note for channel post {post.message_id}")
    # except Exception as e:
    #     logging.error(f"Error updating note: {e}")

    # Update the cloned message in user's chat
    cloned_msg_id = get_cloned_message_id(channel_id, post.message_id)
    if cloned_msg_id:
        try:
            if post.text:
                await context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=cloned_msg_id,
                    text=new_content
                )
            elif post.caption:
                await context.bot.edit_message_caption(
                    chat_id=user_id,
                    message_id=cloned_msg_id,
                    caption=new_content
                )
            logging.info(f"Updated cloned message {cloned_msg_id}")
        except Exception as e:
            logging.error(f"Error updating cloned message: {e}")

# ============================================================================
# Helper Functions
# ============================================================================

def _build_channel_link(post) -> str:
    """
    Build a Telegram link to the channel post.
    
    Args:
        post: Telegram Message object
        
    Returns:
        URL string linking to the post
    """
    channel_id = post.chat.id
    
    # Public channels have a username
    if post.chat.username:
        return f"https://t.me/{post.chat.username}/{post.message_id}"
    
    # Private channels need special formatting
    # Remove -100 prefix for link construction
    cid_str = str(channel_id)
    if cid_str.startswith('-100'):
        cid_str = cid_str[4:]
    return f"https://t.me/c/{cid_str}/{post.message_id}"
