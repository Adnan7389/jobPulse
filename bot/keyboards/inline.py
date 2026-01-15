from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_experience_level_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for experience level selection"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Entry Level", callback_data="junior")],
        [InlineKeyboardButton(text="Mid Level", callback_data="mid")],
        [InlineKeyboardButton(text="Senior Level", callback_data="senior")],
        [InlineKeyboardButton(text="Executive / Lead", callback_data="lead")]
    ])
    return keyboard

def get_category_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for category selection"""
    categories = [
        ('software', 'Software Development'),
        ('marketing', 'Marketing'),
        ('design', 'Design'),
        ('sales', 'Sales'),
        ('finance', 'Finance'),
        ('hr', 'Human Resources'),
        ('customer_service', 'Customer Service'),
        ('management', 'Management'),
        ('other', 'Other'),
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=code)] for code, label in categories
    ])
    return keyboard

def get_work_mode_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for work mode selection"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Remote", callback_data="remote")],
        [InlineKeyboardButton(text="Hybrid", callback_data="hybrid")],
        [InlineKeyboardButton(text="On-site", callback_data="onsite")],
        [InlineKeyboardButton(text="Any / All", callback_data="all")]
    ])
    return keyboard

def get_job_type_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for job type selection"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Full-time", callback_data="full_time")],
        [InlineKeyboardButton(text="Part-time", callback_data="part_time")],
        [InlineKeyboardButton(text="Any / All", callback_data="all")]
    ])
    return keyboard

def get_channel_list_keyboard(channels: list) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with removal buttons for each channel
    
    Args:
        channels: List of channel dictionaries
    """
    keyboard_buttons = []
    
    for channel in channels:
        channel_name = channel.get('name', channel.get('channel_username', 'Unknown'))
        channel_id = channel.get('id')
        
        # Add a row for each channel with a remove button
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"🗑 Remove {channel_name}", 
                callback_data=f"remove_channel_{channel_id}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
def get_featured_channels_keyboard(channels: list, selected_ids: set, done_callback_data: str = "finish_onboarding") -> InlineKeyboardMarkup:
    """
    Create toggleable keyboard for featured channels
    
    Args:
        channels: List of channel dicts from backend
        selected_ids: Set of currently selected channel IDs
        done_callback_data: Callback data for the Done button
    """
    keyboard_buttons = []
    
    for channel in channels:
        c_id = channel.get('id')
        name = channel.get('name') or channel.get('channel_username')
        
        # Determine status icon
        is_selected = c_id in selected_ids
        icon = "✅" if is_selected else "⬜"
        
        button_text = f"{icon} {name}"
        # We need to pass the "context" (onboarding vs addchannel) in the toggle callback?
        # Or we just use a generic toggle callback and handle it based on current state.
        # Let's use generic callback, state separation handles logic.
        callback_data = f"toggle_channel_{c_id}"
        
        keyboard_buttons.append([
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        ])
    
    # Add Finish/Continue button
    current_count = len(selected_ids)
    limit = 5
    finish_text = f"Done ({current_count}/{limit})" if current_count > 0 else "Done"
    
    keyboard_buttons.append([
        InlineKeyboardButton(text=finish_text, callback_data=done_callback_data)
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
