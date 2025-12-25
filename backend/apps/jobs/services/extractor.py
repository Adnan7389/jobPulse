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
    def extract(cls, job_post: JobPost) -> bool:
        """
        Extracts metadata from raw_text and updates the job_post object (Synchronous).
        """
        prompt = f"""
        Role: You are an expert Job Data Analyst at a premium job board.
        Task: Extract structured metadata from the raw job posting text provided below.
        
        Guidelines:
        - Category: Select the best fit from {cls.CATEGORIES}. Use 'software' for developer/engineer roles.
        - Location: Extract City, Country (e.g., "Addis Ababa, Ethiopia"). Use null if unknown.
        - Job Type: {cls.JOB_TYPES}
        - Work Mode: {cls.WORK_MODES}
        
        Example 1 (Raw): "Hiring Python dev. remote. full time"
        Example 1 (JSON): {{"category": "software", "location": null, "job_type": "full_time", "work_mode": "remote"}}
        
        Example 2 (Raw): "Sales manager needed in Dubai. Onsite. Part-time."
        Example 2 (JSON): {{"category": "sales", "location": "Dubai, UAE", "job_type": "part_time", "work_mode": "onsite"}}

        Job Text to Analyze:
        ---
        {job_post.raw_text}
        ---
        Return ONLY valid JSON.
        """

        try:
            metadata = gemini_client.generate_json(prompt)
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
