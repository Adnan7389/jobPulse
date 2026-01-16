from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging

from services.backend_api import submit_feedback

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data.startswith("feedback_"))
async def process_feedback(callback: CallbackQuery):
    """
    Handle feedback buttons (Relevant/Not Relevant)
    Format: feedback_{rel|not}_{notification_id}
    """
    parts = callback.data.split("_")
    if len(parts) < 3:
        return
        
    action = parts[1] # "rel" or "not"
    notification_id = int(parts[2])
    
    feedback_value = "relevant" if action == "rel" else "not_relevant"
    display_value = "👍 Relevant" if action == "rel" else "👎 Not Relevant"
    
    # Send to backend
    success, message = await submit_feedback(notification_id, feedback_value)
    
    if success:
        # Edit message to show confirmation and remove buttons
        # We keep the source link if it exists
        current_markup = callback.message.reply_markup
        new_text = callback.message.text + f"\n\n✅ <b>Feedback Sent:</b> {display_value}"
        
        await callback.message.edit_text(
            new_text,
            reply_markup=None, # Remove buttons to prevent multiple clicks
            parse_mode="HTML"
        )
        await callback.answer(f"Thank you! Feedback saved as {feedback_value}.")
    else:
        await callback.answer("❌ Failed to save feedback. Please try again later.", show_alert=True)
