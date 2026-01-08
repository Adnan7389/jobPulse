import asyncio
import logging
import os
import sys
from telethon import TelegramClient
import config
from services.uploader import Uploader
from services.message_handler import MessageHandler

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SESSION_FILE = os.path.join('session', 'scraper_session')

async def catchup(username, limit=100):
    logger.info(f"🚀 Starting intensive catch-up for @{username} (limit={limit})...")
    
    # Get channel ID from API first to ensure we have the right mapping
    channels = await asyncio.to_thread(Uploader.fetch_channels)
    channel_id = next((c['id'] for c in channels if c['channel_username'] == username), None)
    
    if not channel_id:
        logger.error(f"❌ Channel @{username} not found in Backend API!")
        return

    client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
    await client.start()
    
    count = 0
    errors = 0
    duplicates = 0
    
    async for message in client.iter_messages(username, limit=limit):
        if not message.text:
            continue
            
        job_data = MessageHandler.format_job_data(message, channel_id, username)
        if job_data:
            try:
                # We use the existing uploader but watch for 400s (duplicates)
                url = f"{config.BACKEND_URL}/api/job_posts/"
                import requests
                response = requests.post(url, json=job_data, timeout=10)
                
                if response.status_code in [200, 201]:
                    count += 1
                    logger.info(f"✅ Ingested ID {message.id}")
                elif response.status_code == 400:
                    duplicates += 1
                else:
                    errors += 1
                    logger.error(f"❌ Status {response.status_code}: {response.text}")
            except Exception as e:
                errors += 1
                logger.error(f"Error sending ID {message.id}: {e}")

    logger.info(f"🏁 Finished catch-up for @{username}")
    logger.info(f"📊 Results - New: {count}, Duplicates skipped: {duplicates}, Errors: {errors}")
    
    await client.disconnect()

if __name__ == '__main__':
    target = 'freelance_ethio'
    asyncio.run(catchup(target))
