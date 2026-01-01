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
    logger.info(f"User {message.from_user.id} requested /addchannel")
    
    await message.answer(
        "📢 <b>Add Job Channels</b>\n\n"
        "I'll monitor these channels and notify you of any job matches that fit your profile.\n\n"
        "💡 <b>Batch Add</b>: You can add up to <b>5 channels</b> at once, separated by commas.\n\n"
        "<i>Valid Formats:</i>\n"
        "• <code>@digitaljobs_et, @freelance_ethio</code>\n"
        "• <code>t.me/geezjobs_ethiopia, @utopiajobs</code>\n\n"
        "� <b>Enter channel usernames or links:</b>",
        parse_mode="HTML"
    )
    
    await state.set_state(ChannelStates.waiting_for_channel)
    current_state = await state.get_state()
    logger.info(f"State set to: {current_state}")


# ==================== Process Channel Input ====================
@router.message(ChannelStates.waiting_for_channel)
async def process_channel_input(message: Message, state: FSMContext):
    """Process channel input and add to backend (supports batch)"""
    logger.info(f"Processing channel input: {message.text}")
    
    raw_input = message.text.strip()
    
    if not raw_input:
        await message.answer("⚠️ Please provide at least one channel username or link.")
        return

    # Split by commas for batch addition
    inputs = [i.strip() for i in raw_input.split(',') if i.strip()]
    
    if not inputs:
        await message.answer("⚠️ Please provide at least one valid channel.")
        return

    # Limit batch to 5 to prevent abuse
    if len(inputs) > 5:
        await message.answer("⚠️ You can add at most 5 channels at once. Processing the first 5...")
        inputs = inputs[:5]

    # Show processing message
    processing_msg = await message.answer(f"⏳ Processing {len(inputs)} channel(s)...")
    
    telegram_id = message.from_user.id
    success_profile, user_data, msg = await get_user_profile(telegram_id)
    
    if not success_profile:
        await processing_msg.edit_text(
            "❌ <b>Profile Not Found</b>\n\nPlease complete your profile with /start first.",
            parse_mode="HTML"
        )
        await state.clear()
        return

    user_id = user_data.get('id')
    results = []
    
    for channel_input in inputs:
        try:
            channel_username = normalize_channel_username(channel_input)
            
            if not re.match(r'^[a-zA-Z0-9_]+$', channel_username):
                results.append(f"❌ <code>{channel_input}</code>: Invalid format")
                continue
            
            channel_data = {
                "name": f"@{channel_username}",
                "channel_username": channel_username,
                "added_by": user_id
            }
            
            success, message_text, _ = await add_channel(channel_data)
            
            if success:
                results.append(f"✅ @{channel_username}: Added")
            elif "limit" in message_text.lower():
                results.append(f"🚫 @{channel_username}: Limit reached (Max 5)")
                # Stop processing if limit is reached
                break
            else:
                results.append(f"❌ @{channel_username}: {message_text}")
                
        except Exception as e:
            logger.error(f"Error processing channel {channel_input}: {e}")
            results.append(f"❌ <code>{channel_input}</code>: Error")

    # Construct summary message
    summary = "📊 <b>Batch Addition Results</b>\n\n"
    summary += "\n".join(results)
    summary += "\n\n💡 Use /listchannels to manage your monitored sources."
    
    await processing_msg.edit_text(summary, parse_mode="HTML")
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
