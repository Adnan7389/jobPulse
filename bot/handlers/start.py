from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.onboarding import OnboardingStates

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command and begin onboarding"""
    
    # Clear any existing state
    await state.clear()
    
    welcome_text = (
        "👋 <b>Welcome to JobLens!</b>\n\n"
        "I'll help you find job opportunities that match your skills and preferences. "
        "I monitor Telegram channels 24/7 and send you personalized job alerts.\n\n"
        "📋 <b>Let's set up your profile (takes ~2 minutes):</b>\n"
        "I'll ask you about:\n"
        "• Your skills & keywords\n"
        "• Desired job roles\n"
        "• Experience level\n"
        "• What you're looking for\n\n"
        "Let's get started! 🚀\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 1 of 5: Keywords</b>\n\n"
        "What are your professional skills or keywords?\n\n"
        "<i>Example: Digital Marketing, Sales, Python, Project Management</i>\n\n"
        "💡 Enter your keywords separated by commas:"
    )
    
    await message.answer(welcome_text, parse_mode="HTML")
    await state.set_state(OnboardingStates.waiting_for_skills)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    
    help_text = (
        "🤖 <b>JobLens Help Guide</b>\n\n"
        "Here are the commands you can use:\n\n"
        "<b>Profile & Settings</b>\n"
        "• /start - Create or reset your profile\n"
        "• /myprofile - View your profile summary\n"
        "• /preferences - Edit your preferences (same as /myprofile)\n\n"
        "<b>Channel Monitoring</b>\n"
        "• /addchannel - Add a Telegram channel to monitor\n"
        "• /listchannels - View and manage your channels\n\n"
        "<b>About</b>\n"
        "JobLens monitors Telegram channels for job postings that match your profile keywords."
    )
    
    await message.answer(help_text, parse_mode="HTML")
