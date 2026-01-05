import logging
from typing import Optional, Dict, Any
from shared.utils.ai_request import gemini_client
from ..models import JobPost

logger = logging.getLogger(__name__)

class JobClassifierAndExtractor:
    """
    Unified service that classifies posts as jobs/non-jobs AND extracts metadata.
    
    This combines two operations into ONE AI call for efficiency:
    1. Classification: Is this a job posting? (confidence 0-100)
    2. Extraction: If yes, extract category, location, job_type, work_mode
    
    Cost: Same as original MetadataExtractor (1 AI call per post)
    Benefit: Filters 30-50% of non-job posts before expensive matching
    """
    
    CATEGORIES = [
        'software', 'marketing', 'design', 'sales', 'finance', 
        'hr', 'customer_service', 'management', 'other'
    ]
    
    WORK_MODES = ['remote', 'hybrid', 'onsite']
    JOB_TYPES = ['full_time', 'part_time']
    
    # Confidence threshold for job classification
    CLASSIFICATION_THRESHOLD = 70  # Posts below this are considered non-jobs

    @classmethod
    def extract(cls, job_post: JobPost) -> bool:
        """
        Classifies the post AND extracts metadata using 3-tier Cascade.
        """
        from shared.utils.ai_cascade import AICascade
        
        cascade = AICascade()

        try:
            result, tier_used = cascade.classify_with_fallback(job_post.raw_text)
            
            if not result:
                logger.warning(f"No response from AI Cascade for JobPost {job_post.id}")
                # Default to treating as job (backward compatible)
                job_post.is_job = True
                job_post.classification_confidence = None
                job_post.needs_metadata_extraction = True  # Mark for retry
                job_post.save()
                return True

            # Extract classification results
            is_job = result.get('is_job', True)
            confidence = result.get('confidence', 50)
            
            # Store classification results
            job_post.classification_confidence = confidence
            job_post.ai_tier_classification = tier_used
            
            # Decision logic: Is this a job posting?
            if not is_job or confidence < cls.CLASSIFICATION_THRESHOLD:
                # NOT A JOB - Mark as non-job and exit early
                job_post.is_job = False
                job_post.save()
                logger.info(
                    f"JobPost {job_post.id} classified as NON-JOB "
                    f"(tier={tier_used}, confidence={confidence}%)"
                )
                return False
            
            # IS A JOB - Extract and save metadata
            job_post.is_job = True
            job_post.category = result.get('category') if result.get('category') in cls.CATEGORIES else 'other'
            job_post.location = result.get('location')
            job_post.job_type = result.get('job_type') if result.get('job_type') in cls.JOB_TYPES else None
            job_post.work_mode = result.get('work_mode') if result.get('work_mode') in cls.WORK_MODES else None
            
            # Clear retry flag since extraction succeeded
            job_post.needs_metadata_extraction = False
            
            job_post.save()
            logger.info(
                f"JobPost {job_post.id} classified as JOB by {tier_used.upper()} "
                f"(confidence={confidence}%, category={job_post.category})"
            )
            return True

        except Exception as e:
            logger.error(f"Classification/extraction failed for JobPost {job_post.id}: {e}")
            # On error, default to treating as job (backward compatible)
            job_post.is_job = True
            job_post.classification_confidence = None
            job_post.needs_metadata_extraction = True  # Mark for retry
            job_post.save()
            return True


# Backward compatibility alias
MetadataExtractor = JobClassifierAndExtractor

