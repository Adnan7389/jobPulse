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
    
    # Start the dynamic channel monitor in the background
    asyncio.create_task(channel_monitor_loop(client))
    
    logger.info("Initialization complete. Scraper is running and monitoring for new channels...")
    
    # 3. Keep the process alive
    await client.run_until_disconnected()

async def refresh_channels(client):
    """Fetch tracked channels from API and join any new ones."""
    global channel_map
    try:
        logger.info("Refreshing target channels from API...")
        channels = await asyncio.to_thread(Uploader.fetch_channels)
        
        if not channels:
            logger.warning("No channels returned from API.")
            return

        new_channels_count = 0
        for channel in channels:
            username = channel.get('channel_username')
            channel_id = channel.get('id')
            
            if username and username not in channel_map:
                # New channel detected!
                channel_map[username] = channel_id
                # Ensure joined
                success = await ChannelJoiner.ensure_joined(client, username)
                if success:
                    logger.info(f"Successfully joined and started monitoring: {username} (ID: {channel_id})")
                    new_channels_count += 1
                else:
                    # Remove from map if join failed so we retry next time
                    del channel_map[username]
            elif not username:
                logger.warning(f"Channel ID {channel_id} has no username. Skipping.")
                
        if new_channels_count > 0:
            logger.info(f"Added {new_channels_count} new channels to monitor.")
            
    except Exception as e:
        logger.error(f"Error during channel refresh: {e}")

async def channel_monitor_loop(client):
    """Background loop to periodically refresh channels."""
    while True:
        await refresh_channels(client)
        # Wait 5 minutes (300 seconds) before checking again
        await asyncio.sleep(300)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraper stopped by user.")
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")