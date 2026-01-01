import logging
import httpx
from celery import shared_task
from celery.exceptions import Retry
from django.conf import settings
from .models import Notification

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_notification_to_user(self, notification_id):
    """
    Asynchronously sends a notification to a user via the Telegram Bot service.
    """
    try:
        notification = Notification.objects.select_related('user', 'job').get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found.")
        return

    user = notification.user
    job = notification.job

    if not user.telegram_id:
        logger.warning(f"User {user.id} has no telegram_id. Skipping notification.")
        return

    payload = {
        "notification_id": notification.id,
        "telegram_id": user.telegram_id,
        "job_post": {
            "id": job.id,
            "category": job.category,
            "location": job.location,
            "job_type": job.job_type,
            "work_mode": job.work_mode,
            "source_link": job.source_link,
            "raw_text_preview": job.raw_text[:500] if job.raw_text else ""
        },
        "match": {
            "score": notification.match_score,
            "reasoning": notification.reasoning
        }
    }

    # Internal Bot API endpoint
    bot_api_url = f"{settings.BOT_INTERNAL_URL}/notify"

    try:
        # Use a synchronous client here because Celery workers are usually synchronous
        # If using eventlet/gevent, httpx.AsyncClient would be better, but standard Celery is prefork.
        headers = {
            "X-Bot-API-Secret": os.getenv("BOT_API_SECRET", "")
        }
        with httpx.Client(timeout=10.0) as client:
            response = client.post(bot_api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                notification.is_sent = True
                notification.save(update_fields=['is_sent'])
                logger.info(f"Successfully sent notification {notification_id} to user {user.telegram_id}")
            elif response.status_code == 429:
                # Rate limited by bot service (FloodWait)
                retry_after = int(response.headers.get("Retry-After", 30))
                logger.warning(f"Rate limited by Bot API. Retrying in {retry_after}s. Notification: {notification_id}")
                raise self.retry(countdown=retry_after)
            else:
                logger.error(f"Bot API returned error {response.status_code}: {response.text}")
                raise Exception(f"Bot API error: {response.status_code}")

    except (httpx.RequestError, Exception) as exc:
        # Avoid double-wrapping the retry exception
        if isinstance(exc, Retry):
            raise exc
        
        logger.error(f"Failed to send notification {notification_id}: {exc}")
        # Exponential backoff: 60, 120, 240 seconds
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)
