from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from states.onboarding import OnboardingStates
from keyboards.inline import (
    get_experience_level_keyboard, 
    get_category_keyboard, 
    get_work_mode_keyboard, 
    get_job_type_keyboard
)
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
            "⚠️ Please enter at least one skill or keyword.\n\n"
            "<i>Example: Marketing, Excel, Python, Sales</i>",
            parse_mode="HTML"
        )
        return
    
    # Store in FSM context
    await state.update_data(skills=skills)
    
    # Move to next step
    await message.answer(
        f"✅ Great! Saved {len(skills)} skill(s).\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 2 of 8: Job Titles</b>\n\n"
        "What job roles are you interested in?\n\n"
        "<i>Example: Accountant, Sales Manager, Data Analyst, Developer</i>\n\n"
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
            "<i>Example: Project Manager, Designer, Engineer</i>",
            parse_mode="HTML"
        )
        return
    
    # Store in FSM context
    await state.update_data(job_titles=job_titles)
    
    # Move to next step with inline keyboard
    await message.answer(
        f"✅ Great! Saved {len(job_titles)} job title(s).\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 3 of 8: Experience Level</b>\n\n"
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
        'junior': 'Entry Level',
        'mid': 'Mid Level',
        'senior': 'Senior Level',
        'lead': 'Executive / Lead'
    }
    
    # Store in FSM context
    await state.update_data(experience_level=experience_level)
    
    # Answer callback to remove loading state
    await callback.answer()
    
    # Edit the message to show selection
    await callback.message.edit_text(
        f"✅ Experience level: <b>{level_display.get(experience_level, experience_level)}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 4 of 8: Years of Experience</b>\n\n"
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
    
    # Move to Category Selection
    await message.answer(
        f"✅ Great! {years} years of experience.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 5 of 8: Target Category</b>\n\n"
        "Which job category best describes what you are looking for?\n\n"
        "👇 Select one category:",
        reply_markup=get_category_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OnboardingStates.waiting_for_preferred_category)


# ==================== Preferred Category Handler ====================
@router.callback_query(OnboardingStates.waiting_for_preferred_category)
async def process_preferred_category(callback: CallbackQuery, state: FSMContext):
    """Process category selection"""
    
    category = callback.data
    
    categories = {
        'software': 'Software Development',
        'marketing': 'Marketing',
        'design': 'Design',
        'sales': 'Sales',
        'finance': 'Finance',
        'hr': 'Human Resources',
        'customer_service': 'Customer Service',
        'management': 'Management',
        'other': 'Other',
    }
    
    await state.update_data(preferred_category=category)
    await callback.answer()
    
    await callback.message.edit_text(
        f"✅ Category: <b>{categories.get(category, category)}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 6 of 8: Work Mode</b>\n\n"
        "What is your preferred work mode?\n\n"
        "👇 Select one (or Any/All):",
        reply_markup=get_work_mode_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OnboardingStates.waiting_for_preferred_mode)


# ==================== Preferred Mode Handler ====================
@router.callback_query(OnboardingStates.waiting_for_preferred_mode)
async def process_preferred_mode(callback: CallbackQuery, state: FSMContext):
    """Process work mode selection"""
    
    mode = callback.data
    modes = {
        'remote': 'Remote',
        'hybrid': 'Hybrid',
        'onsite': 'On-site',
        'all': 'Any / All'
    }
    
    await state.update_data(preferred_mode=mode)
    await callback.answer()
    
    await callback.message.edit_text(
        f"✅ Work Mode: <b>{modes.get(mode, mode)}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 7 of 8: Job Type</b>\n\n"
        "What type of job are you looking for?\n\n"
        "👇 Select one (or Any/All):",
        reply_markup=get_job_type_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OnboardingStates.waiting_for_preferred_type)


# ==================== Preferred Type Handler ====================
@router.callback_query(OnboardingStates.waiting_for_preferred_type)
async def process_preferred_type(callback: CallbackQuery, state: FSMContext):
    """Process job type selection"""
    
    job_type = callback.data
    types = {
        'full_time': 'Full-time',
        'part_time': 'Part-time',
        'all': 'Any / All'
    }
    
    await state.update_data(preferred_type=job_type)
    await callback.answer()
    
    await callback.message.edit_text(
        f"✅ Job Type: <b>{types.get(job_type, job_type)}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 8 of 8: About You (Bio)</b>\n\n"
        "Tell me what kind of job you're looking for. This helps me find the best matches for you!\n\n"
        "<i>Example: Looking for remote Marketing opportunities with a focus on social media.</i>\n\n"
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
            "<i>Example: Looking for remote opportunities in sales or management</i>",
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
            f"✅ <b>Profile Saved Successfully!</b>\n\n"
            f"{response_message}\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 <b>Your Profile Summary:</b>\n"
            f"• <b>Skills:</b> {', '.join(user_data['skills'])}\n"
            f"• <b>Job Titles:</b> {', '.join(user_data['job_titles'])}\n"
            f"• <b>Experience:</b> {user_data['experience_level']} ({user_data['years_experience']} years)\n"
            f"• <b>Category:</b> {user_data.get('preferred_category', 'Not set').title()}\n"
            f"• <b>Mode:</b> {user_data.get('preferred_mode', 'Not set').title()}\n"
            f"• <b>Job Type:</b> {user_data.get('preferred_type', 'Not set').title()}\n"
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
