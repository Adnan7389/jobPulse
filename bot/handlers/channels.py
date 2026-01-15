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
    normalize_channel_username,
    get_featured_channels
)
from keyboards.inline import get_channel_list_keyboard, get_featured_channels_keyboard

router = Router()
logger = logging.getLogger(__name__)

# ==================== Add Channel Command ====================
@router.message(Command("addchannel"))
async def cmd_add_channel(message: Message, state: FSMContext):
    """Handle /addchannel command - Show Featured + Manual Option"""
    logger.info(f"User {message.from_user.id} requested /addchannel")
    
    # 1. Fetch User Profile
    success, user_data, msg = await get_user_profile(message.from_user.id)
    if not success:
        await message.answer(f"❌ {msg}\nPlease use /start")
        return

    user_id = user_data.get('id')

    # 2. Fetch User's Current Channels
    _, current_channels, _ = await get_user_channels(user_id)
    current_ids = {c['id'] for c in current_channels} if current_channels else set()

    # 3. Fetch Featured Channels
    f_success, featured, f_msg = await get_featured_channels()
    
    if not f_success or not featured:
        # Fallback to manual only if API fails
        await message.answer("📢 <b>Add Channels</b>\n\n💡 Enter channel username (e.g. @ethiojobs):", parse_mode="HTML")
        await state.set_state(ChannelStates.waiting_for_channel)
        return

    # 4. Filter and Prepare State
    initial_selection = []
    
    # Pre-select channels the user already has
    for f in featured:
        if f['id'] in current_ids:
            initial_selection.append(f['id'])
            
    await state.update_data(
        available_channels=featured,
        selected_channel_ids=initial_selection,
        original_selection=list(initial_selection)
    )
    
    await message.answer(
        "📢 <b>Add Job Channels</b>\n\n"
        "Select from our <b>Verified List</b> below OR type a username manually.\n\n"
        "<i>Accepted formats:</i>\n"
        "• <code>@username</code>\n"
        "• <code>t.me/username</code>\n"
        "• <code>https://t.me/username</code>\n\n"
        "<i>(Green check ✅ means you are already subscribed)</i>",
        reply_markup=get_featured_channels_keyboard(
            featured, 
            set(initial_selection), 
            done_callback_data="finish_channel_add"
        ),
        parse_mode="HTML"
    )
    
    await state.set_state(ChannelStates.waiting_for_channel)


# ==================== Toggle Featured Channel ====================
@router.callback_query(ChannelStates.waiting_for_channel, F.data.startswith("toggle_channel_"))
async def process_channel_toggle_add(callback: CallbackQuery, state: FSMContext):
    """Toggle channel selection in /addchannel mode"""
    
    channel_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    
    selected_ids = set(data.get('selected_channel_ids', []))
    available = data.get('available_channels', [])
    
    # Toggle logic
    if channel_id in selected_ids:
        selected_ids.remove(channel_id)
    else:
        if len(selected_ids) >= 5:
            await callback.answer("⚠️ Limit reached! (Max 5)", show_alert=True)
            return
        selected_ids.add(channel_id)
    
    # Update State
    await state.update_data(selected_channel_ids=list(selected_ids))
    
    # Update UI
    await callback.message.edit_reply_markup(
        reply_markup=get_featured_channels_keyboard(
            available, 
            selected_ids, 
            done_callback_data="finish_channel_add"
        )
    )
    
    await callback.answer()


# ==================== Finish / Done Button ====================
@router.callback_query(ChannelStates.waiting_for_channel, F.data == "finish_channel_add")
async def process_channel_done(callback: CallbackQuery, state: FSMContext):
    """Commit changes from /addchannel selection"""
    
    data = await state.get_data()
    selected = set(data.get('selected_channel_ids', []))
    original = set(data.get('original_selection', []))
    available = data.get('available_channels', [])
    
    to_add = selected - original
    to_remove = original - selected
    
    if not to_add and not to_remove:
        await callback.message.edit_text("✅ No changes made.")
        await state.clear()
        return

    await callback.message.edit_text("⏳ Saving changes...")
    
    # Get User ID
    success, user_data, _ = await get_user_profile(callback.from_user.id)
    if not success:
        return
    user_id = user_data.get('id')
    
    results = []
    
    # Process Additions
    for c_id in to_add:
        c_info = next((c for c in available if c['id'] == c_id), None)
        if c_info:
            ok, msg, _ = await add_channel({
                'name': c_info['name'],
                'channel_username': c_info['channel_username'],
                'channel_id': c_info['channel_id'],
                'added_by': user_id
            })
            if ok:
                results.append(f"✅ Subscribed to {c_info['name']}")
    
    # Process Removals
    for c_id in to_remove:
        c_info = next((c for c in available if c['id'] == c_id), None)
        name = c_info['name'] if c_info else "Channel"
        ok, msg = await remove_channel(c_id, user_id)
        if ok:
            results.append(f"❌ Unsubscribed from {name}")

    summary = "\n".join(results)
    await callback.message.edit_text(
        f"<b>Updates Saved!</b>\n\n{summary}\n\n💡 Use /listchannels to see all.", 
        parse_mode="HTML"
    )
    await state.clear()


# ==================== Process Manual Channel Input ====================
@router.message(ChannelStates.waiting_for_channel)
async def process_channel_input(message: Message, state: FSMContext):
    """Process channel input and add to backend (supports batch)"""
    logger.info(f"Processing manual channel input: {message.text}")
    
    raw_input = message.text.strip()
    
    if not raw_input:
        await message.answer("⚠️ Please provide at least one channel username or link.")
        return

    # Split by commas for batch addition
    inputs = [i.strip() for i in raw_input.split(',') if i.strip()]
    
    if not inputs:
        await message.answer("⚠️ Please provide at least one valid channel.")
        return

    if len(inputs) > 5:
        await message.answer("⚠️ You can add at most 5 channels at once. Processing the first 5...")
        inputs = inputs[:5]

    processing_msg = await message.answer(f"⏳ Processing {len(inputs)} channel(s)...")
    
    telegram_id = message.from_user.id
    success_profile, user_data, msg = await get_user_profile(telegram_id)
    
    if not success_profile:
        await processing_msg.edit_text("❌ Profile Not Found. Use /start.")
        await state.clear()
        return

    user_id = user_data.get('id')
    results = []
    
    for channel_input in inputs:
        try:
            channel_username = normalize_channel_username(channel_input)
            
            if len(channel_username) < 5:
                results.append(f"❌ <code>{channel_input}</code>: Too short (min 5 chars)")
                continue

            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]+$', channel_username):
                results.append(f"❌ <code>{channel_input}</code>: Invalid format (must start with a letter)")
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
                break
            else:
                results.append(f"❌ @{channel_username}: {message_text}")
                
        except Exception as e:
            logger.error(f"Error processing channel {channel_input}: {e}")
            results.append(f"❌ Error: {channel_input}")

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
    processing_msg = await message.answer("⏳ Fetching your channels...")
    
    success, user_data, msg = await get_user_profile(telegram_id)
    if not success:
        await processing_msg.edit_text(f"❌ {msg}\nPlease use /start")
        return
    
    user_id = user_data.get('id')
    success, channels, msg = await get_user_channels(user_id)
    
    if not success:
        await processing_msg.edit_text(f"❌ Failed to fetch channels: {msg}")
        return
    
    if not channels:
        await processing_msg.edit_text(
            "📢 <b>No Channels Yet</b>\n\n"
            "You haven't added any channels to monitor.\n\n"
            "💡 Use /addchannel to start monitoring job channels!",
            parse_mode="HTML"
        )
        return
    
    channels_text = "📢 <b>Your Monitored Channels</b>\n\n"
    for idx, channel in enumerate(channels, 1):
        channel_name = channel.get('name', channel.get('channel_username', 'Unknown'))
        status = "✅ Active" if channel.get('is_active', True) else "⏸ Inactive"
        channels_text += f"{idx}. {channel_name} - {status}\n"
    
    channels_text += f"\n<b>Total:</b> {len(channels)}/5 channel(s)\n\n"
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
    channel_id = int(callback.data.split("_")[-1])
    await callback.answer("Removing channel...")
    
    user_success, user_data, _ = await get_user_profile(callback.from_user.id)
    if not user_success:
        return
        
    user_id = user_data.get('id')
    success, message_text = await remove_channel(channel_id, user_id)
    
    if success:
        # Refresh list
        c_success, channels, _ = await get_user_channels(user_id)
        if c_success and channels:
            channels_text = "📢 <b>Your Monitored Channels</b>\n\n"
            for idx, channel in enumerate(channels, 1):
                channel_name = channel.get('name', channel.get('channel_username', 'Unknown'))
                status = "✅ Active" if channel.get('is_active', True) else "⏸ Inactive"
                channels_text += f"{idx}. {channel_name} - {status}\n"
            
            channels_text += f"\n<b>Total:</b> {len(channels)}/5 channel(s)\n\n"
            await callback.message.edit_text(
                channels_text + "✅ Removed successfully!",
                reply_markup=get_channel_list_keyboard(channels),
                parse_mode="HTML"
            )
        else:
             await callback.message.edit_text(
                "✅ <b>Channel Removed!</b>\n\n📢 <b>No Channels Left</b>\n\nUse /addchannel to add more.",
                parse_mode="HTML"
            )
    else:
        await callback.message.edit_text(f"❌ Failed to remove: {message_text}")
