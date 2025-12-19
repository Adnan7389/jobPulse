import logging

logger = logging.getLogger(__name__)

class MessageHandler:
    @staticmethod
    def format_job_data(message, channel_id, channel_username):
        """Format Telegram message into JobPost data structure."""
        if not message or not getattr(message, 'text', None):
            return None
            
        if not channel_username:
            # Source must come ONLY from event.chat.username (or channel_username)
            # If missing → skip ingestion to ensure traceability and compliance.
            return None

        source_link = f"https://t.me/{channel_username}/{message.id}"
        
        return {
            "channel_id": channel_id,
            "message_id": message.id,
            "raw_text": message.text,
            "source_link": source_link,
            "source_channel": channel_username,
            "date": message.date.isoformat() if message.date else None
        }
