from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import logging

from services.backend_api import get_user_profile

router = Router()
logger = logging.getLogger(__name__)

# ==================== My Profile Command ====================
@router.message(Command("myprofile"))
async def cmd_my_profile(message: Message):
    """Handle /myprofile command to view user profile"""
    
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
        'junior': 'Junior',
        'mid': 'Mid-level',
        'senior': 'Senior',
        'lead': 'Lead/Principal'
    }
    exp_level_raw = user_data.get('experience_level', '')
    exp_level = level_map.get(exp_level_raw, exp_level_raw.title())
    
    years_exp = user_data.get('years_experience', 0)
    bio = user_data.get('bio', 'No bio provided')
    
    # Create profile message
    profile_text = (
        "👤 <b>Your JobPulse Profile</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛠 <b>Skills:</b>\n{skills}\n\n"
        f"💼 <b>Desired Roles:</b>\n{job_titles}\n\n"
        f"📈 <b>Experience Level:</b>\n{exp_level}\n\n"
        f"⏳ <b>Years of Experience:</b>\n{years_exp} years\n\n"
        f"📝 <b>Bio / Looking For:</b>\n{bio}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💡 <b>Want to update your profile?</b>\n"
        "You can update your skills and preferences by running the onboarding again."
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
    """Handle edit profile button - essentially triggers /start"""
    await callback.answer()
    
    # Import locally to avoid circular imports if any, 
    # though start handler should be registered in main
    # Here we just send a message guiding user to /start or trigger it manually if needed.
    # Simpler to just tell them:
    
    await callback.message.answer(
        "🔄 <b>Update Profile</b>\n\n"
        "To update your profile, we'll go through the setup steps again. "
        "This ensures all your data is fresh!\n\n"
        "👉 Click /start to begin.",
        parse_mode="HTML"
    )

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
