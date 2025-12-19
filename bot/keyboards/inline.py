from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_experience_level_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard for experience level selection"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Junior", callback_data="junior")],
        [InlineKeyboardButton(text="Mid", callback_data="mid")],
        [InlineKeyboardButton(text="Senior", callback_data="senior")],
        [InlineKeyboardButton(text="Lead", callback_data="lead")]
    ])
    return keyboard
