from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from states.onboarding import OnboardingStates
from keyboards.inline import get_experience_level_keyboard
from services.backend_api import create_user_profile

router = Router()
logger = logging.getLogger(__name__)

# ==================== Skills Handler ====================
@router.message(OnboardingStates.waiting_for_skills)
async def process_skills(message: Message, state: FSMContext):
    """Process skills input"""
    
    # Parse comma-separated skills
    skills_text = message.text.strip()
    skills = [skill.strip() for skill in skills_text.split(',') if skill.strip()]
    
    # Validate at least one skill
    if not skills:
        await message.answer(
            "⚠️ Please enter at least one skill.\n\n"
            "<i>Example: Python, Django, React</i>",
            parse_mode="HTML"
        )
        return
    
    # Store in FSM context
    await state.update_data(skills=skills)
    
    # Move to next step
    await message.answer(
        f"✅ Great! Saved {len(skills)} skill(s).\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 2 of 5: Job Titles</b>\n\n"
        "What job roles are you interested in?\n\n"
        "<i>Example: Backend Developer, DevOps Engineer, Python Developer</i>\n\n"
        "💡 Enter job titles separated by commas:",
        parse_mode="HTML"
    )
    await state.set_state(OnboardingStates.waiting_for_job_titles)


# ==================== Job Titles Handler ====================
@router.message(OnboardingStates.waiting_for_job_titles)
async def process_job_titles(message: Message, state: FSMContext):
    """Process job titles input"""
    
    # Parse comma-separated job titles
    titles_text = message.text.strip()
    job_titles = [title.strip() for title in titles_text.split(',') if title.strip()]
    
    # Validate at least one job title
    if not job_titles:
        await message.answer(
            "⚠️ Please enter at least one job title.\n\n"
            "<i>Example: Backend Developer, Full Stack Engineer</i>",
            parse_mode="HTML"
        )
        return
    
    # Store in FSM context
    await state.update_data(job_titles=job_titles)
    
    # Move to next step with inline keyboard
    await message.answer(
        f"✅ Great! Saved {len(job_titles)} job title(s).\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 3 of 5: Experience Level</b>\n\n"
        "What's your experience level?\n\n"
        "👇 Select from the options below:",
        reply_markup=get_experience_level_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OnboardingStates.waiting_for_experience_level)


# ==================== Experience Level Handler ====================
@router.callback_query(OnboardingStates.waiting_for_experience_level)
async def process_experience_level(callback: CallbackQuery, state: FSMContext):
    """Process experience level selection from inline keyboard"""
    
    experience_level = callback.data  # junior, mid, senior, lead
    
    # Map to display names
    level_display = {
        'junior': 'Junior',
        'mid': 'Mid-level',
        'senior': 'Senior',
        'lead': 'Lead/Principal'
    }
    
    # Store in FSM context
    await state.update_data(experience_level=experience_level)
    
    # Answer callback to remove loading state
    await callback.answer()
    
    # Edit the message to show selection
    await callback.message.edit_text(
        f"✅ Experience level: <b>{level_display.get(experience_level, experience_level)}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 4 of 5: Years of Experience</b>\n\n"
        "How many years of professional experience do you have?\n\n"
        "💡 Enter a number (0-50):",
        parse_mode="HTML"
    )
    
    await state.set_state(OnboardingStates.waiting_for_years_experience)


# ==================== Years of Experience Handler ====================
@router.message(OnboardingStates.waiting_for_years_experience)
async def process_years_experience(message: Message, state: FSMContext):
    """Process years of experience input"""
    
    # Validate numeric input
    try:
        years = int(message.text.strip())
        
        if years < 0 or years > 50:
            await message.answer(
                "⚠️ Please enter a valid number between 0 and 50.\n\n"
                "💡 Example: 3"
            )
            return
        
    except ValueError:
        await message.answer(
            "⚠️ Please enter a number (not text).\n\n"
            "💡 Example: 3"
        )
        return
    
    # Store in FSM context
    await state.update_data(years_experience=years)
    
    # Move to final step
    await message.answer(
        f"✅ Great! {years} years of experience.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 5 of 5: About You</b>\n\n"
        "Tell me what kind of job you're looking for. This helps me find the best matches for you!\n\n"
        "<i>Example: Looking for remote Django opportunities with a focus on API development and microservices. "
        "Interested in fintech or healthcare domains.</i>\n\n"
        "💡 Write a short bio about what you're seeking:",
        parse_mode="HTML"
    )
    await state.set_state(OnboardingStates.waiting_for_bio)


# ==================== Bio Handler (Final Step) ====================
@router.message(OnboardingStates.waiting_for_bio)
async def process_bio(message: Message, state: FSMContext):
    """Process bio and create user profile in backend"""
    
    bio = message.text.strip()
    
    # Validate bio is not empty
    if not bio:
        await message.answer(
            "⚠️ Please tell me a bit about what you're looking for.\n\n"
            "<i>Example: Looking for remote opportunities in backend development</i>",
            parse_mode="HTML"
        )
        return
    
    # Store bio
    await state.update_data(bio=bio)
    
    # Retrieve all collected data
    user_data = await state.get_data()
    
    # Add telegram_id
    user_data['telegram_id'] = message.from_user.id
    
    # Show processing message
    processing_msg = await message.answer("⏳ Creating your profile...")
    
    # Submit to backend
    success, response_message = await create_user_profile(user_data)
    
    if success:
        # Clear FSM state
        await state.clear()
        
        await processing_msg.edit_text(
            f"✅ <b>Profile Created Successfully!</b>\n\n"
            f"{response_message}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 <b>Your Profile Summary:</b>\n"
            f"• <b>Skills:</b> {', '.join(user_data['skills'])}\n"
            f"• <b>Job Titles:</b> {', '.join(user_data['job_titles'])}\n"
            f"• <b>Experience:</b> {user_data['experience_level']} ({user_data['years_experience']} years)\n"
            f"• <b>Looking for:</b> {bio[:100]}{'...' if len(bio) > 100 else ''}\n\n"
            "🔔 I'll start monitoring channels and send you personalized job alerts!\n\n"
            "💡 <b>Next Steps:</b>\n"
            "• Use /addchannel to add Telegram job channels to monitor\n"
            "• Use /preferences to update your profile\n"
            "• Use /history to see your job matches",
            parse_mode="HTML"
        )
        
        logger.info(f"Successfully onboarded user {message.from_user.id}")
    
    else:
        # Error occurred
        await processing_msg.edit_text(
            f"❌ <b>Profile Creation Failed</b>\n\n"
            f"{response_message}\n\n"
            "Please try again with /start",
            parse_mode="HTML"
        )
        
        # Clear state so user can restart
        await state.clear()
        
        logger.error(f"Failed to onboard user {message.from_user.id}: {response_message}")
