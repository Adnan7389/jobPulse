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
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    rate_limit='5/m'         # Lowered to 5/m to leave room for matching tasks
)
def process_new_job_post(self, job_id):
    """
    Background task to process a new job post using AI extraction and matching.
    Includes Task Resilience: Auto-retries, Exponential Backoff.
    
    Pipeline:
    1. Classify + Extract metadata (MetadataExtractor)
       - Determines if post is a job (is_job field)
       - Extracts metadata only if it's a job
    2. If is_job=True: Run matching pipeline
    3. If is_job=False: Exit early (skip expensive matching)
    """
    try:
        job = JobPost.objects.get(id=job_id)
        logger.info(f"Starting processing for Job #{job_id} (Attempt {self.request.retries + 1})")
        
        # 1. AI Classification + Metadata Extraction
        # Returns True if it's a job post, False if it's not
        is_job = MetadataExtractor.extract(job)
        
        if not is_job:
            # NOT A JOB - Exit early without matching
            # This saves expensive AI matching on announcements, spam, etc.
            job.is_processed = True
            job.save()
            logger.info(
                f"Job #{job_id} classified as NON-JOB. "
                f"Skipping matching pipeline (confidence={job.classification_confidence}%)"
            )
            return  # Early exit
        
        # IS A JOB - Check if metadata extraction failed and needs retry
        if job.needs_metadata_extraction:
            logger.warning(f"AI extraction failed for Job #{job_id}. Skipping matching until metadata is available.")
            # Schedule retry task
            retry_metadata_extraction.apply_async(
                args=[job_id],
                countdown=3600  # Retry in 1 hour
            )
            return # IMPORTANT: Do not proceed to matching if metadata is missing/quota hit
        
        logger.info(
            f"Job #{job_id} classified as JOB. "
            f"Proceeding to matching (confidence={job.classification_confidence}%)"
        )
        
        # 2. Run Matching Orchestrator (only for verified jobs)
        MatchOrchestrator.run(job)
        
        # Mark as processed (if we didn't schedule a retry, or even if we did, 
        # it's 'processed' for now but might be updated later)
        job.is_processed = True
        job.save()
        logger.info(f"Finished processing for Job #{job_id}")
        
    except JobPost.DoesNotExist:
        logger.error(f"JobPost with id {job_id} does not exist.")
    except Exception as e:
        logger.error(f"Retryable error processing Job #{job_id}: {e}")
        # Re-raise to trigger Celery autoretry
        raise e

@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=3600,
    autoretry_for=(Exception,),
    retry_backoff=True,
    rate_limit='2/m'          # Lowered to 2/m to be very conservative on retries
)
def retry_metadata_extraction(self, job_id):
    """
    Background task to retry AI metadata extraction if it failed initially (e.g., quota).
    If extraction succeeds, it also re-runs the matching pipeline for better accuracy.
    """
    try:
        job = JobPost.objects.get(id=job_id)
        if not job.needs_metadata_extraction:
            logger.info(f"Job #{job_id} no longer needs metadata extraction. Skipping.")
            return

        logger.info(f"Retrying metadata extraction for Job #{job_id} (Attempt {self.request.retries + 1})")
        
        # Attempt extraction again
        success = MetadataExtractor.extract(job)
        
        if success and not job.needs_metadata_extraction:
            logger.info(f"Successfully extracted metadata for Job #{job_id} on retry.")
            # Re-run matching pipeline now that we have better metadata (category, etc.)
            MatchOrchestrator.run(job)
            logger.info(f"Re-run matching orchestrator for Job #{job_id} with improved metadata.")
        else:
            logger.warning(f"Retry extraction for Job #{job_id} failed again or still missing metadata.")
            # Celery will autoretry based on the decorator settings
            
    except JobPost.DoesNotExist:
        logger.error(f"JobPost with id {job_id} does not exist for retry.")
    except Exception as e:
        logger.error(f"Error during metadata extraction retry for Job #{job_id}: {e}")
        raise e

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    rate_limit='10/m'         # Limit matching requests to 10 per minute
)
def process_semantic_match(self, user_id, job_id):
    """
    Independent task to perform semantic matching for a single user/job pair.
    This allows us to throttle AI matching requests separately from extraction.
    """
    from apps.users.models import User
    from apps.notifications.models import Notification
    from apps.notifications.tasks import send_notification_to_user
    
    try:
        user = User.objects.get(id=user_id)
        job = JobPost.objects.get(id=job_id)
        
        # Call the orchestrator logic for single user matching
        score, reasoning = MatchOrchestrator.get_semantic_match(user, job)
        
        if score >= MatchOrchestrator.MATCH_THRESHOLD:
            notification = Notification.objects.create(
                user=user,
                job=job,
                match_score=score,
                reasoning=reasoning,
                source='gemini'
            )
            send_notification_to_user.apply_async(args=[notification.id], countdown=2)
            logger.info(f"Notification created for User {user_id} on Job {job_id}")
            
    except (User.DoesNotExist, JobPost.DoesNotExist):
        logger.error(f"User {user_id} or Job {job_id} missing for matching.")
    except Exception as e:
        logger.error(f"Match task failed for User {user_id} on Job {job_id}: {e}")
        raise e
