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
