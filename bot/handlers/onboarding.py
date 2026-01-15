from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import logging

from states.onboarding import OnboardingStates
from keyboards.inline import (
    get_experience_level_keyboard, 
    get_category_keyboard, 
    get_featured_channels_keyboard
)
from services.backend_api import (
    create_user_profile, 
    get_featured_channels, 
    add_channel, # To subscribe to selected channels
    get_user_profile # To get user ID after creation
)

router = Router()
logger = logging.getLogger(__name__)

# ==================== Step 1: Bio (Start) ====================
# This handler should be triggered by /start command in main.py
# But we need a handler to catch the bio input if state is set.

@router.message(OnboardingStates.waiting_for_bio)
async def process_bio(message: Message, state: FSMContext):
    """Process bio input (Step 1)"""
    
    bio = message.text.strip()
    
    if not bio or len(bio) < 10:
        await message.answer(
            "⚠️ Please include your skills and what you're looking for (at least 10 chars).\n\n"
            "<i>Example: Graphic Designer skilled in Photoshop, Illustrator, and UI Design looking for freelance work.</i>",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(bio=bio)
    
    await message.answer(
        f"✅ Got it!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 2 of 4: Category</b>\n\n"
        "Which category best fits your interest?\n\n"
        "👇 Select one category:",
        reply_markup=get_category_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OnboardingStates.waiting_for_preferred_category)


# ==================== Step 2: Category ====================
@router.callback_query(OnboardingStates.waiting_for_preferred_category)
async def process_category(callback: CallbackQuery, state: FSMContext):
    """Process category selection (Step 2)"""
    
    category = callback.data
    # Determine 'category_name' for display
    # (Simplified for now, can map if needed)
    
    await state.update_data(preferred_category=category)
    await callback.answer()
    
    await callback.message.edit_text(
        f"✅ Category: <b>{category.replace('_', ' ').title()}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Question 3 of 4: Experience Level</b>\n\n"
        "What is your experience level?\n\n"
        "👇 Select one:",
        reply_markup=get_experience_level_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(OnboardingStates.waiting_for_experience_level)


# ==================== Step 3: Experience ====================
@router.callback_query(OnboardingStates.waiting_for_experience_level)
async def process_experience(callback: CallbackQuery, state: FSMContext):
    """Process experience selection (Step 3)"""
    
    level = callback.data
    await state.update_data(experience_level=level)
    
    # Defaults for removed steps to keep backend happy
    await state.update_data(
        years_experience=1 if level == 'junior' else 3, # Dummy defaults
        preferred_mode='all',
        preferred_type='all',
        skills=[], # AI will extract from Bio
        job_titles=[] # AI will extract from Bio
    )
    
    await callback.answer()
    
    # Fetch Featured Channels based on category
    data = await state.get_data()
    category = data.get('preferred_category')
    
    success, channels, msg = await get_featured_channels(category)
    
    if not success or not channels:
        # Skip channel selection if fetch fails
        await finish_onboarding(callback.message, state)
        return

    # Initialize selected channels list in FSM
    await state.update_data(
        available_channels=channels,
        selected_channel_ids=[]
    )
    
    await callback.message.edit_text(
        f"✅ Experience: <b>{level.title()}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "<b>Final Step: Verified Channels</b>\n\n"
        "Select channels to subscribe to using the buttons below.\n"
        "Click 'Done' when finished.",
        reply_markup=get_featured_channels_keyboard(channels, set()), # Start with empty set
        parse_mode="HTML"
    )
    await state.set_state(OnboardingStates.waiting_for_channels)


# ==================== Step 4: Featured Channels ====================
@router.callback_query(OnboardingStates.waiting_for_channels, F.data.startswith("toggle_channel_"))
async def process_channel_toggle(callback: CallbackQuery, state: FSMContext):
    """Toggle channel selection"""
    
    channel_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    selected_ids = set(data.get('selected_channel_ids', []))
    channels = data.get('available_channels', [])
    
    if channel_id in selected_ids:
        selected_ids.remove(channel_id)
    else:
        if len(selected_ids) >= 5:
            await callback.answer("⚠️ Limit reached! (Max 5)", show_alert=True)
            return
        selected_ids.add(channel_id)
    
    # Save back to state
    await state.update_data(selected_channel_ids=list(selected_ids))
    
    # Update keyboard
    await callback.message.edit_reply_markup(
        reply_markup=get_featured_channels_keyboard(channels, selected_ids)
    )
    await callback.answer()


@router.callback_query(OnboardingStates.waiting_for_channels, F.data == "finish_onboarding")
async def process_finish_button(callback: CallbackQuery, state: FSMContext):
    """Finish onboarding button clicked"""
    await callback.answer()
    await finish_onboarding(callback.message, state, from_callback=True)


async def finish_onboarding(message: Message, state: FSMContext, from_callback=False):
    """Finalize onboarding and submit data"""
    
    user_data = await state.get_data()
    user_data['telegram_id'] = message.chat.id # Use chat.id which is same as user.id in private chats
    
    if from_callback:
        processing_msg = await message.edit_text("⏳ Creating your profile...")
    else:
        processing_msg = await message.answer("⏳ Creating your profile...")
    
    # 1. Create Profile
    success, response_msg = await create_user_profile(user_data)
    
    if not success:
        await processing_msg.edit_text(
            f"❌ <b>Profile Creation Failed</b>\n\n{response_msg}\n\nTry /start again.",
            parse_mode="HTML"
        )
        await state.clear()
        return

    # 2. Subscribe to selected channels
    selected_ids = user_data.get('selected_channel_ids', [])
    channels = user_data.get('available_channels', [])
    
    # We need to get the user's DB ID to link subscriptions.
    # Since create_user_profile doesn't return the ID, we fetch the profile now.
    fetch_success, profile_data, _ = await get_user_profile(user_data['telegram_id'])
    
    if fetch_success and profile_data:
        user_db_id = profile_data['id']
        
        # Subscribe loop
        for c_id in selected_ids:
            # Find channel info
            channel_info = next((c for c in channels if c['id'] == c_id), None)
            if channel_info:
                # Add/Subscribe
                await add_channel({
                    'name': channel_info['name'],
                    'channel_username': channel_info['channel_username'],
                    'channel_id': channel_info['channel_id'],
                    'added_by': user_db_id
                })
    
    await state.clear()
    
    await processing_msg.edit_text(
        f"✅ <b>Profile Ready!</b>\n\n"
        f"🎯 <b>Bio:</b> {user_data.get('bio')}\n"
        f"📂 <b>Category:</b> {user_data.get('preferred_category')}\n"
        f"📺 <b>Subscribed:</b> {len(selected_ids)} channels\n\n"
        "🔔 I'll start sending you matching jobs immediately!\n\n"
        "💡 <b>Tip:</b> If results are generic, edit your Bio in /preferences.",
        parse_mode="HTML"
    )
