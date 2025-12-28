import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from config import config
from handlers import start, onboarding, channels, profile
from services.notification_sender import NotificationSender
from services.api import create_app
from aiohttp import web

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

async def main():
    """Main bot entry point"""
    
    # Initialize Redis Storage
    # Create Redis client from URL if available (handles SSL/auth automatically)
    redis_url = os.getenv('REDIS_URL') or os.getenv('CELERY_BROKER_URL')
    
    if redis_url:
        logger.info(f"Connecting to Redis using URL (masked): {redis_url[:15]}...")
        redis_client = Redis.from_url(redis_url)
    else:
        # Fallback to host/port (legacy)
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_client = Redis(host=redis_host, port=redis_port, db=0)
    
    # Test Redis connection
    try:
        await redis_client.ping()
        logger.info("✅ Connected to Redis successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Redis: {e}")
        return

    storage = RedisStorage(redis=redis_client)
    
    # Initialize Bot and Dispatcher
    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=storage)
    
    # Register routers
    dp.include_router(start.router)
    dp.include_router(onboarding.router)
    dp.include_router(channels.router)
    dp.include_router(profile.router)
    
    logger.info("Bot started successfully")
    logger.info(f"Backend URL: {config.backend_url}")
    
    # Initialize Notification Service & API
    notification_sender = NotificationSender(bot)
    api_app = await create_app(notification_sender)
    runner = web.AppRunner(api_app)
    await runner.setup()
    
    # Listen on all interfaces (internal port)
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    await site.start()
    logger.info("✅ Internal Notification API started on port 8080")

    # Robust polling loop
    while True:
        try:
            logger.info("Start polling")
            await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
        except Exception as e:
            logger.error(f"Error during polling: {e}")
            logger.info("Restarting polling in 5 seconds...")
            await asyncio.sleep(5)
        finally:
             # If start_polling returns normally (e.g. signal), we might want to exit or just loop.
             # Usually logging is enough.
             logger.info("Polling loop ended (or crashed), checking...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
