import logging
from typing import Optional, Dict, Any
from shared.utils.ai_request import gemini_client
from ..models import JobPost

logger = logging.getLogger(__name__)

class MetadataExtractor:
    CATEGORIES = [
        'software', 'marketing', 'design', 'sales', 'finance', 
        'hr', 'customer_service', 'management', 'other'
    ]
    
    WORK_MODES = ['remote', 'hybrid', 'onsite']
    JOB_TYPES = ['full_time', 'part_time']

    @classmethod
    async def extract(cls, job_post: JobPost) -> bool:
        """
        Extracts metadata from raw_text and updates the job_post object.
        """
        prompt = f"""
        Extract job metadata from the following job posting text. 
        Return ONLY a JSON object with the following fields:
        - category: One of {cls.CATEGORIES}
        - location: City/Country or null if not found
        - job_type: One of {cls.JOB_TYPES} or null if not found
        - work_mode: One of {cls.WORK_MODES} or null if not found

        Job Text:
        ---
        {job_post.raw_text}
        ---
        """

        try:
            metadata = await gemini_client.generate_json(prompt)
            if not metadata:
                logger.warning(f"No metadata extracted for JobPost {job_post.id}")
                return False

            # Update JobPost fields
            job_post.category = metadata.get('category') if metadata.get('category') in cls.CATEGORIES else 'other'
            job_post.location = metadata.get('location')
            job_post.job_type = metadata.get('job_type') if metadata.get('job_type') in cls.JOB_TYPES else None
            job_post.work_mode = metadata.get('work_mode') if metadata.get('work_mode') in cls.WORK_MODES else None
            
            job_post.save()
            logger.info(f"Successfully extracted metadata for JobPost {job_post.id}")
            return True

        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return False
