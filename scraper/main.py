import asyncio
import logging
import os
import sys
from telethon import TelegramClient
import config
from services.uploader import Uploader
from services.message_handler import MessageHandler

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

async def process_channel(client, channel):
    """Scrape messages from a single channel."""
    channel_id = channel.get('id')
    channel_username = channel.get('channel_username') 
    last_scraped_id = channel.get('last_scraped_id', 0)
    
    if not channel_username:
        logger.warning(f"Channel ID {channel_id} has no username. Skipping.")
        return

    logger.info(f"Processing channel: {channel_username} (Last Scraped ID: {last_scraped_id})")

    try:
        # Resolve the channel entity
        entity = await client.get_entity(channel_username)
        
        # Determine constraints for fetching
        kwargs = {}
        if last_scraped_id and last_scraped_id > 0:
            kwargs['min_id'] = last_scraped_id
            kwargs['limit'] = None # Fetch all new messages
        else:
            kwargs['limit'] = 50 # First run

        message_count = 0
        async for message in client.iter_messages(entity, **kwargs):
            job_data = MessageHandler.format_job_data(message, channel_id, channel_username)
            if job_data:
                # Send to backend
                success = await asyncio.to_thread(Uploader.send_job_post, job_data)
                if success:
                    message_count += 1
        
        logger.info(f"Finished processing {channel_username}. Scraped {message_count} messages.")

    except Exception as e:
        logger.error(f"Error processing channel {channel_username}: {e}")

async def main():
    logger.info("Starting JobPulse Scraper...")
    
    if not config.API_ID or not config.API_HASH:
        logger.error("API_ID and API_HASH not found. Check your environment variables.")
        return

    # Initialize Telethon Client
    # The session file will be stored in scraper/session/
    client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
    
    try:
        await client.start()
    except Exception as e:
        logger.critical(f"Failed to start Telegram Client: {e}")
        return

    logger.info("Telegram Client connected successfully.")

    while True:
        logger.info("Fetching channels to scrape...")
        channels = await asyncio.to_thread(Uploader.fetch_channels)
        
        if not channels:
            logger.info("No channels found or API error. Waiting 60 seconds.")
            await asyncio.sleep(60)
            continue
            
        for channel in channels:
            await process_channel(client, channel)
        
        logger.info("Cycle complete. Sleeping for 300 seconds.")
        await asyncio.sleep(300)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraper stopped by user.")