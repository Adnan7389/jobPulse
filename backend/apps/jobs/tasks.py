import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from apps.jobs.models import JobPost
from apps.notifications.models import Notification

from asgiref.sync import async_to_sync
from .services.extractor import MetadataExtractor
from .services.orchestrator import MatchOrchestrator

logger = logging.getLogger(__name__)

@shared_task
def process_new_job_post(job_id):
    """
    Background task to process a new job post using AI extraction and matching.
    """
    try:
        job = JobPost.objects.get(id=job_id)
        logger.info(f"Starting processing for Job #{job_id}")
        
        # 1. AI Metadata Extraction
        async_to_sync(MetadataExtractor.extract)(job)
        
        # 2. Run Matching Orchestrator
        async_to_sync(MatchOrchestrator.run)(job)
        
        # Mark as processed
        job.is_processed = True
        job.save()
        logger.info(f"Finished processing for Job #{job_id}")
        
    except JobPost.DoesNotExist:
        logger.error(f"JobPost with id {job_id} does not exist.")
    except Exception as e:
        logger.exception(f"Unexpected error processing Job #{job_id}: {e}")
