from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import logging

from services.backend_api import get_user_profile

router = Router()
logger = logging.getLogger(__name__)

# ==================== My Profile / Preferences Command ====================
@router.message(Command("myprofile"))
@router.message(Command("preferences"))
@router.message(Command("update"))
async def cmd_my_profile(message: Message, state: FSMContext = None):
    """Handle /myprofile, /preferences, and /update command"""
    
    if message.text.startswith('/update') and state:
        # If user explicitly typed /update, start the onboarding flow immediately
        await state.clear()
        from handlers.start import cmd_start
        return await cmd_start(message, state)
    
    telegram_id = message.from_user.id
    
    # Show processing message
    processing_msg = await message.answer("⏳ Fetching your profile...")
    
    # Fetch user profile
    success, user_data, msg = await get_user_profile(telegram_id)
    
    if not success:
        await processing_msg.edit_text(
            f"❌ <b>Profile Not Found</b>\n\n"
            f"{msg}\n\n"
            f"Please create your profile first with /start",
            parse_mode="HTML"
        )
        return
    
    # Format profile data
    skills = ", ".join(user_data.get('skills', [])) or "None listed"
    job_titles = ", ".join(user_data.get('job_titles', [])) or "None listed"
    
    # Map experience level to display name
    level_map = {
        'junior': 'Entry Level',
        'mid': 'Mid Level',
        'senior': 'Senior Level',
        'lead': 'Executive / Lead'
    }
    exp_level_raw = user_data.get('experience_level', '')
    exp_level = level_map.get(exp_level_raw, exp_level_raw.title())
    
    years_exp = user_data.get('years_experience', 0)
    bio = user_data.get('bio', 'No bio provided')
    
    # Create profile message
    profile_text = (
        "👤 <b>Your JobLens Profile</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛠 <b>Skills:</b>\n{skills}\n\n"
        f"💼 <b>Desired Roles:</b>\n{job_titles}\n\n"
        f"🎯 <b>Filter Category:</b>\n{user_data.get('preferred_category', 'Not set').title()}\n\n"
        f"🌐 <b>Work Mode:</b>\n{user_data.get('preferred_mode', 'Not set').title()}\n\n"
        f"📉 <b>Experience Level:</b>\n{exp_level}\n\n"
        f"⏳ <b>Years of Experience:</b>\n{years_exp} years\n\n"
        f"📝 <b>Bio / Looking For:</b>\n{bio}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    # Inline keyboard for actions
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Edit Profile (Restart)", callback_data="edit_profile_start")],
        [InlineKeyboardButton(text="📢 Manage Channels", callback_data="view_channels")]
    ])
    
    await processing_msg.edit_text(
        profile_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ==================== Profile Actions Handlers ====================

@router.callback_query(F.data == "edit_profile_start")
async def handle_edit_profile(callback: CallbackQuery, state: FSMContext):
    from handlers.start import cmd_start
    await cmd_start(callback.message, state)

@router.callback_query(F.data == "view_channels")
async def handle_view_channels(callback: CallbackQuery):
    """Handle view channels button - triggers /listchannels logic (redirect)"""
    await callback.answer()
    
    # We can't easily call the command handler directly without a message object
    # So we guide them to the command
    await callback.message.answer(
        "📢 <b>Manage Channels</b>\n\n"
        "👉 Click /listchannels to view and remove your monitored channels.\n"
        "👉 Click /addchannel to add a new one.",
        parse_mode="HTML"
    )
