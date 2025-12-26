import logging
import html
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest

logger = logging.getLogger(__name__)

class NotificationSender:
    def __init__(self, bot: Bot):
        self.bot = bot

    def format_message(self, data: dict) -> str:
        job = data['job_post']
        match = data['match']
        
        category = job.get('category', 'General').replace('_', ' ').title()
        mode = job.get('work_mode', 'N/A').title()
        location = job.get('location', 'N/A')
        
        # HTML Escaping for safety
        reasoning = html.escape(match.get('reasoning', ''))
        preview = html.escape(job.get('raw_text_preview', '')[:300])
        
        # Determine score icon
        score = match.get('score', 0)
        score_icon = "🟢" if score >= 85 else "🟡" if score >= 70 else "⚪"
        
        message = (
            f"<b>{score_icon} JobPulse Match Found!</b>\n\n"
            f"🏷️ <b>{category}</b> | <b>{mode}</b>\n"
            f"📍 {location}\n\n"
            f"🤖 <b>AI Match Score: {score}%</b>\n"
            f"<i>{reasoning}</i>\n\n"
            f"📑 <b>Job Preview:</b>\n"
            f"<code>{preview}...</code>\n"
        )
        return message

    def get_keyboard(self, source_link: str) -> InlineKeyboardMarkup:
        if not source_link:
            return None
        
        button = InlineKeyboardButton(text="🔗 View Original Post", url=source_link)
        return InlineKeyboardMarkup(inline_keyboard=[[button]])

    async def send_notification(self, data: dict) -> bool:
        """
        Sends the notification to the user.
        Returns True on success, False on recoverable failure, 
        or raises FloodWait (RetryAfter) if rate limited.
        """
        telegram_id = data['telegram_id']
        message_text = self.format_message(data)
        keyboard = self.get_keyboard(data['job_post'].get('source_link'))
        
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return True
        except TelegramRetryAfter as e:
            # Re-raise to be handled by the API layer (which will return 429 to backend)
            logger.warning(f"Flood limit reached for {telegram_id}. Retry after {e.retry_after}s")
            raise e
        except TelegramForbiddenError:
            logger.warning(f"User {telegram_id} blocked the bot. Skipping.")
            return True # Treat as success to stop retries
        except TelegramBadRequest as e:
            logger.error(f"Bad request for user {telegram_id}: {e}. Payload might be malformed.")
            return True # Malformed message should not be retried indefinitely
        except Exception as e:
            logger.exception(f"Unexpected error sending to {telegram_id}: {e}")
            return False
