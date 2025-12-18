import logging

logger = logging.getLogger(__name__)

class MessageHandler:
    @staticmethod
    def format_job_data(message, channel_id, channel_username):
        """Format Telegram message into JobPost data structure."""
        if not message or not getattr(message, 'text', None):
            return None
            
        # Construct source link
        # Use entity username if available, otherwise fallback to channel_username
        username = channel_username
        if hasattr(message, 'peer_id') and hasattr(message.peer_id, 'channel_id'):
            # This is more complex to resolve without entity, 
            # so we rely on the passed username for now.
            pass
            
        source_link = f"https://t.me/{username}/{message.id}"
        
        return {
            "channel_id": channel_id,
            "message_id": message.id,
            "raw_text": message.text,
            "source_link": source_link,
            "date": message.date.isoformat() if message.date else None
        }
