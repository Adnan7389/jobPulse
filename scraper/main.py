import asyncio
import logging
import os
import sys
from telethon import TelegramClient, events
import config
from services.uploader import Uploader
from services.message_handler import MessageHandler
from services.channel_joiner import ChannelJoiner

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Directory for session files
SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'session')
os.makedirs(SESSION_DIR, exist_ok=True)
SESSION_FILE = os.path.join(SESSION_DIR, 'scraper_session')

# Global map of channel_username -> channel_id
channel_map = {}

async def main():
    logger.info("Starting JobPulse Scraper (Real-time Monitoring)...")
    
    if not config.API_ID or not config.API_HASH:
        logger.error("API_ID and API_HASH not found. Check your environment variables.")
        return

    # Initialize Telethon Client
    client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)

    @client.on(events.NewMessage)
    async def handle_new_message(event):
        try:
            # 1. Block DMs, Groups, and Private chats (Hard security boundary)
            # Use Telethon metadata to ensure we only process broadcast channels.
            if not event.is_channel:
                return
                
            # 2. Public-Channel-Only Guard
            # Private or non-public sources must never be scraped to ensure 
            # absolute compliance with Telegram TOS and data privacy.
            chat = await event.get_chat()
            if not getattr(chat, 'broadcast', False) or not getattr(chat, 'username', None):
                return
                
            username = chat.username

            # 3. Check Denylist (Skip ingestion if on blocked list)
            if username in config.DENYLIST:
                return

            # 4. Enforce Source Attribution (Check tracked channels)
            if username in channel_map:
                channel_id = channel_map[username]
                logger.info(f"New message from tracked channel: {username}")
                
                job_data = MessageHandler.format_job_data(event.message, channel_id, username)
                if job_data:
                    # Push to API immediately
                    success = await asyncio.to_thread(Uploader.send_job_post, job_data)
                    if success:
                        logger.info(f"Successfully ingested job from {username} (Message ID: {event.message.id})")
            
        except Exception as e:
            logger.error(f"Error handling new message event: {e}")

    try:
        await client.start()
    except Exception as e:
        logger.critical(f"Failed to start Telegram Client: {e}")
        return

    logger.info("Telegram Client connected successfully.")

    # 1. Fetch tracked channels from API
    logger.info("Fetching target channels from API...")
    channels = await asyncio.to_thread(Uploader.fetch_channels)
    
    if not channels:
        logger.warning("No channels returned from API. Scraper will wait for new messages but might not have filters.")
    
    # 2. Join channels and populate map
    for channel in channels:
        username = channel.get('channel_username')
        channel_id = channel.get('id')
        
        if username:
            channel_map[username] = channel_id
            # Ensure bot is a member
            await ChannelJoiner.ensure_joined(client, username)
            logger.info(f"Monitoring: {username} (ID: {channel_id})")
        else:
            logger.warning(f"Channel ID {channel_id} has no username. Cannot monitor.")

    logger.info(f"Initialization complete. Monitoring {len(channel_map)} channels. Listening for events...")
    
    # 3. Keep the process alive
    await client.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraper stopped by user.")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")