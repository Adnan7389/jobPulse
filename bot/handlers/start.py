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
        "👋 <b>Welcome to JobPulse!</b>\n\n"
        "I'll help you find job opportunities that match your skills and preferences. "
        "I monitor Telegram channels 24/7 and send you personalized job alerts.\n\n"
        "📋 <b>Let's set up your profile (takes ~2 minutes):</b>\n"
        "I'll ask you about:\n"
        "• Your technical skills\n"
        "• Desired job roles\n"
        "• Experience level\n"
        "• What you're looking for\n\n"
        "Let's get started! 🚀\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 1 of 5: Skills</b>\n\n"
        "What technologies and tools do you know?\n\n"
        "<i>Example: Python, Django, PostgreSQL, Docker, REST APIs</i>\n\n"
        "💡 Enter your skills separated by commas:"
    )
    
    await message.answer(welcome_text, parse_mode="HTML")
    await state.set_state(OnboardingStates.waiting_for_skills)
