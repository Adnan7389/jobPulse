from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from states.onboarding import OnboardingStates

router = Router()

@router.message(Command("start"))
@router.message(Command("setup"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start or /setup command and begin onboarding"""
    
    # Clear any existing state
    await state.clear()
    
    welcome_text = (
        "👋 <b>Welcome to JobLens!</b>\n\n"
        "I'll help you find job opportunities that match your skills and preferences. "
        "I monitor Telegram channels 24/7 and send you personalized job alerts.\n\n"
        "📋 <b>Profile Setup (Just 4 Steps!)</b>\n"
        "1. Tell me about what you're looking for (Bio)\n"
        "2. Choose your customized category\n"
        "3. Set your experience level\n"
        "4. Select verified channels to follow\n\n"
        "Let's get started! 🚀\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Step 1 of 4: About You (Bio & Skills)</b>\n\n"
        "Tell me about your profession and key skills.\n\n"
        "<i>Example A: I'm a Marketing Manager skilled in SEO, Content Strategy, and Google Ads looking for full-time roles.</i>\n\n"
        "<i>Example B: Python Developer experienced in Django and React seeking remote projects.</i>\n\n"
        "💡 Write your bio below (don't forget to list your top skills!):"
    )
    
    await message.answer(welcome_text, parse_mode="HTML")
    await state.set_state(OnboardingStates.waiting_for_bio)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    
    help_text = (
        "🤖 <b>JobLens Help Guide</b>\n\n"
        "Here are the commands you can use:\n\n"
        "<b>Profile & Settings</b>\n"
        "• /start - Start or reset your profile\n"
        "• /setup - Quick alias to setup/reset profile\n"
        "• /update - Update your existing profile\n"
        "• /myprofile - View your current profile summary\n"
        "• /preferences - Edit your preferences\n\n"
        "<b>Channel Monitoring</b>\n"
        "• /addchannel - Add a Telegram channel to monitor\n"
        "• /listchannels - View and manage your channels\n\n"
        "<b>About</b>\n"
        "JobLens monitors Telegram channels for job postings that match your profile keywords."
    )
    
    await message.answer(help_text, parse_mode="HTML")
