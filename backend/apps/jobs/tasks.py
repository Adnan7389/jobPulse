import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from apps.jobs.models import JobPost
from apps.notifications.models import Notification

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task
def process_new_job_post(job_id):
    """
    Background task to process a new job post.
    For Day 7, this just logs and creates a dummy notification.
    """
    try:
        job = JobPost.objects.get(id=job_id)
        logger.info(f"Starting processing for Job #{job_id}")
    except JobPost.DoesNotExist:
        logger.error(f"JobPost with id {job_id} does not exist.")
        return

    # Dummy logic for Day 7: Notify the first user we find
    user = User.objects.first()
    if not user:
        logger.warning("No users found in database. Cannot create dummy notification.")
        return

    # Idempotency: Check if notification already exists
    if Notification.objects.filter(user=user, job=job).exists():
        logger.info(f"Notification already exists for Job #{job.id} and User {user.username}. Skipping.")
        return

    # Create dummy notification
    Notification.objects.create(user=user, job=job)
    logger.info(f"Success: Created dummy Notification for Job #{job.id} -> User {user.username}")
