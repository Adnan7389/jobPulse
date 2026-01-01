import logging
import os
from aiohttp import web
from aiogram.exceptions import TelegramRetryAfter
from services.notification_sender import NotificationSender

logger = logging.getLogger(__name__)

async def handle_notify(request):
    """
    HTTP handler for incoming notification requests from the backend.
    """
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400, text="Invalid JSON")

    # Security check: Verify API Secret
    expected_secret = os.getenv("BOT_API_SECRET")
    if expected_secret:
        received_secret = request.headers.get("X-Bot-API-Secret")
        if received_secret != expected_secret:
            logger.warning(f"Unauthorized notification attempt from {request.remote}")
            return web.Response(status=401, text="Unauthorized")
    
    sender: NotificationSender = request.app['notification_sender']
    notification_id = data.get('notification_id', 'unknown')
    
    logger.info(f"Received notification request for ID: {notification_id}")
    
    try:
        success = await sender.send_notification(data)
        if success:
            return web.Response(status=200, text="OK")
        else:
            return web.Response(status=500, text="Internal Error")
    except TelegramRetryAfter as e:
        # Pass the FloodWait info back to Celery
        logger.warning(f"Propagating FloodWait: {e.retry_after}s for Notification {notification_id}")
        return web.Response(
            status=429, 
            text=f"Retry After {e.retry_after}",
            headers={"Retry-After": str(e.retry_after)}
        )
    except Exception as e:
        logger.exception(f"Error handling notification {notification_id}")
        return web.Response(status=500, text=str(e))

async def create_app(notification_sender: NotificationSender):
    """
    Creates the aiohttp application with the notification sender service.
    """
    app = web.Application()
    app['notification_sender'] = notification_sender
    app.router.add_post('/notify', handle_notify)
    return app
