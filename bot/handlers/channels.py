from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import logging
import re

from states.channels import ChannelStates
from services.backend_api import (
    get_user_profile, 
    add_channel, 
    get_user_channels, 
    remove_channel,
    normalize_channel_username
)
from keyboards.inline import get_channel_list_keyboard

router = Router()
logger = logging.getLogger(__name__)

# ==================== Add Channel Command ====================
@router.message(Command("addchannel"))
async def cmd_add_channel(message: Message, state: FSMContext):
    """Handle /addchannel command"""
    
    await message.answer(
        "📢 <b>Add a Telegram Channel to Monitor</b>\n\n"
        "I'll start monitoring job postings from this channel and send you personalized matches.\n\n"
        "<i>Examples of valid formats:</i>\n"
        "• @ethiojobs\n"
        "• https://t.me/ethiojobs\n"
        "• t.me/ethiojobs\n"
        "• ethiojobs\n\n"
        "💡 <b>Enter the channel username or link:</b>",
        parse_mode="HTML"
    )
    
    await state.set_state(ChannelStates.waiting_for_channel)


# ==================== Process Channel Input ====================
@router.message(ChannelStates.waiting_for_channel)
async def process_channel_input(message: Message, state: FSMContext):
    """Process channel input and add to backend"""
    
    channel_input = message.text.strip()
    
    # Validate input is not empty
    if not channel_input:
        await message.answer(
            "⚠️ Please provide a valid channel username or link.\n\n"
            "<i>Example: @ethiojobs</i>",
            parse_mode="HTML"
        )
        return
    
    # Normalize the channel username
    try:
        channel_username = normalize_channel_username(channel_input)
    except Exception as e:
        logger.error(f"Error normalizing channel: {e}")
        await message.answer(
            "❌ Invalid channel format. Please try again.\n\n"
            "<i>Example: @ethiojobs or t.me/ethiojobs</i>",
            parse_mode="HTML"
        )
        return
    
    # Validate channel username format (alphanumeric and underscores)
    if not re.match(r'^[a-zA-Z0-9_]+$', channel_username):
        await message.answer(
            "❌ Invalid channel username. Channel names can only contain letters, numbers, and underscores.\n\n"
            "<i>Example: @ethiojobs</i>",
            parse_mode="HTML"
        )
        return
    
    # Show processing message
    processing_msg = await message.answer("⏳ Adding channel...")
    
    # Get user profile to get user ID
    telegram_id = message.from_user.id
    success, user_data, msg = await get_user_profile(telegram_id)
    
    if not success:
        await processing_msg.edit_text(
            "❌ <b>Profile Not Found</b>\n\n"
            "Please complete your profile setup first with /start",
            parse_mode="HTML"
        )
        await state.clear()
        return
    
    user_id = user_data.get('id')
    
    # Prepare channel data
    # Note: We're not fetching channel_id from Telegram API here (that's the Scraper's job)
    # The bot does lightweight validation, Scraper does authoritative verification
    channel_data = {
        "name": f"@{channel_username}",  # Human readable name
        "channel_username": channel_username,  # Without @
        "added_by": user_id
    }
    
    # Add channel via API
    success, message_text, channel_id = await add_channel(channel_data)
    
    if success:
        await processing_msg.edit_text(
            f"✅ <b>Channel Added Successfully!</b>\n\n"
            f"📢 <b>Channel:</b> @{channel_username}\n\n"
            f"I'll start monitoring this channel for job postings and send you personalized alerts!\n\n"
            f"💡 <b>Tip:</b> Use /listchannels to see all your monitored channels.",
            parse_mode="HTML"
        )
        logger.info(f"User {telegram_id} added channel @{channel_username}")
    else:
        await processing_msg.edit_text(
            f"❌ <b>Failed to Add Channel</b>\n\n"
            f"{message_text}\n\n"
            f"Please try again or use /help for assistance.",
            parse_mode="HTML"
        )
    
    # Clear state
    await state.clear()


# ==================== List Channels Command ====================
@router.message(Command("listchannels"))
async def cmd_list_channels(message: Message):
    """Handle /listchannels command"""
    
    telegram_id = message.from_user.id
    
    # Show processing message
    processing_msg = await message.answer("⏳ Fetching your channels...")
    
    # Get user profile to get user ID
    success, user_data, msg = await get_user_profile(telegram_id)
    
    if not success:
        await processing_msg.edit_text(
            "❌ <b>Profile Not Found</b>\n\n"
            "Please complete your profile setup first with /start",
            parse_mode="HTML"
        )
        return
    
    user_id = user_data.get('id')
    
    # Fetch user's channels
    success, channels, msg = await get_user_channels(user_id)
    
    if not success:
        await processing_msg.edit_text(
            f"❌ <b>Failed to Fetch Channels</b>\n\n"
            f"{msg}\n\n"
            f"Please try again later.",
            parse_mode="HTML"
        )
        return
    
    if not channels or len(channels) == 0:
        await processing_msg.edit_text(
            "📢 <b>No Channels Yet</b>\n\n"
            "You haven't added any channels to monitor.\n\n"
            "💡 Use /addchannel to start monitoring job channels!",
            parse_mode="HTML"
        )
        return
    
    # Display channels with removal buttons
    channels_text = "📢 <b>Your Monitored Channels</b>\n\n"
    
    for idx, channel in enumerate(channels, 1):
        channel_name = channel.get('name', channel.get('channel_username', 'Unknown'))
        status = "✅ Active" if channel.get('is_active', True) else "⏸ Inactive"
        channels_text += f"{idx}. {channel_name} - {status}\n"
    
    channels_text += f"\n<b>Total:</b> {len(channels)} channel(s)\n\n"
    channels_text += "💡 Tap a button below to remove a channel:"
    
    await processing_msg.edit_text(
        channels_text,
        reply_markup=get_channel_list_keyboard(channels),
        parse_mode="HTML"
    )


# ==================== Remove Channel Callback ====================
@router.callback_query(F.data.startswith("remove_channel_"))
async def callback_remove_channel(callback: CallbackQuery):
    """Handle channel removal callback"""
    
    # Extract channel ID from callback data
    channel_id = int(callback.data.split("_")[-1])
    
    # Answer callback immediately
    await callback.answer("Removing channel...")
    
    # Remove channel via API
    success, message_text = await remove_channel(channel_id)
    
    if success:
        # Refresh the channel list
        telegram_id = callback.from_user.id
        
        # Get user profile
        user_success, user_data, _ = await get_user_profile(telegram_id)
        
        if user_success:
            user_id = user_data.get('id')
            
            # Fetch updated channels list
            channels_success, channels, _ = await get_user_channels(user_id)
            
            if channels_success and channels and len(channels) > 0:
                # Update message with new list
                channels_text = "📢 <b>Your Monitored Channels</b>\n\n"
                
                for idx, channel in enumerate(channels, 1):
                    channel_name = channel.get('name', channel.get('channel_username', 'Unknown'))
                    status = "✅ Active" if channel.get('is_active', True) else "⏸ Inactive"
                    channels_text += f"{idx}. {channel_name} - {status}\n"
                
                channels_text += f"\n<b>Total:</b> {len(channels)} channel(s)\n\n"
                channels_text += "✅ Channel removed successfully!\n\n"
                channels_text += "💡 Tap a button below to remove another channel:"
                
                await callback.message.edit_text(
                    channels_text,
                    reply_markup=get_channel_list_keyboard(channels),
                    parse_mode="HTML"
                )
            else:
                # No more channels
                await callback.message.edit_text(
                    "✅ <b>Channel Removed!</b>\n\n"
                    "📢 <b>No Channels Left</b>\n\n"
                    "You have no monitored channels.\n\n"
                    "💡 Use /addchannel to start monitoring job channels!",
                    parse_mode="HTML"
                )
        else:
            # Just show success message
            await callback.message.edit_text(
                f"✅ <b>Channel Removed Successfully!</b>\n\n"
                f"Use /listchannels to see your updated channel list.",
                parse_mode="HTML"
            )
    else:
        await callback.message.edit_text(
            f"❌ <b>Failed to Remove Channel</b>\n\n"
            f"{message_text}\n\n"
            f"Please try again later.",
            parse_mode="HTML"
        )
    
    logger.info(f"User {callback.from_user.id} attempted to remove channel_id={channel_id}: {message_text}")
