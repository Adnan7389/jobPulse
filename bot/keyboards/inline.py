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
