import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from apps.jobs.models import JobPost
from apps.notifications.models import Notification

from asgiref.sync import async_to_sync
from .services.extractor import MetadataExtractor
from .services.orchestrator import MatchOrchestrator

logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Part 4: Retries must be delayed (initial 60s)
    autoretry_for=(Exception,),
    retry_backoff=True,      # Part 4: Use backoff to reduce cascading failures
    retry_jitter=True        # Add jitter to avoid thundering herd on recovery
)
def process_new_job_post(self, job_id):
    """
    Background task to process a new job post using AI extraction and matching.
    Includes Task Resilience: Auto-retries, Exponential Backoff.
    """
    try:
        job = JobPost.objects.get(id=job_id)
        logger.info(f"Starting processing for Job #{job_id} (Attempt {self.request.retries + 1})")
        
        # 1. AI Metadata Extraction
        MetadataExtractor.extract(job)
        
        # 2. Run Matching Orchestrator
        MatchOrchestrator.run(job)
        
        # Mark as processed
        job.is_processed = True
        job.save()
        logger.info(f"Finished processing for Job #{job_id}")
        
    except JobPost.DoesNotExist:
        logger.error(f"JobPost with id {job_id} does not exist.")
    except Exception as e:
        logger.error(f"Retryable error processing Job #{job_id}: {e}")
        # Re-raise to trigger Celery autoretry
        raise e
