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
        Classifies the post AND extracts metadata (Synchronous).
        
        Returns:
            True if this is a job post (and metadata was extracted)
            False if this is NOT a job post (no metadata extraction)
        
        Side Effects:
            - Sets job_post.is_job and job_post.classification_confidence
            - If is_job=True: Sets category, location, job_type, work_mode
            - Saves the job_post to database
        """
        
        prompt = f"""
        Role: You are an expert Job Data Analyst at a premium job board.
        
        Task 1: JOB CLASSIFICATION
        Determine if this post is a JOB POSTING or NOT.
        
        A JOB POSTING contains:
        - Hiring intent (e.g., "hiring", "recruiting", "vacancy", "position available")
        - Job requirements or qualifications
        - Application instructions (e.g., "apply", "send CV", contact email/phone)
        - Job title or role description
        
        NOT a job posting:
        - General announcements (e.g., "Happy holidays!", "Channel rules")
        - Spam or promotional content
        - News or articles
        - Greetings or casual messages
        
        Task 2: METADATA EXTRACTION (only if it IS a job posting)
        If the post is a job, extract structured metadata.
        
        Guidelines for Metadata:
        - Category: Select the best fit from {cls.CATEGORIES}. Use 'software' for developer/engineer roles.
        - Location: Extract "City, Country" (e.g., "Addis Ababa, Ethiopia"). Use null if not mentioned.
        - Job Type: {cls.JOB_TYPES}. Use null if not mentioned.
        - Work Mode: {cls.WORK_MODES}. Use null if not mentioned.
        
        Example 1 (JOB POSTING - Remote Software Role):
        Raw: "We're hiring a Python developer! Remote work. Full-time position. Apply: jobs@company.com"
        JSON: {{
            "is_job": true,
            "confidence": 95,
            "category": "software",
            "location": null,
            "job_type": "full_time",
            "work_mode": "remote"
        }}
        
        Example 2 (JOB POSTING - Sales Role in Dubai):
        Raw: "Sales manager needed in Dubai. Onsite. Part-time. Send CV to hiring@example.ae"
        JSON: {{
            "is_job": true,
            "confidence": 90,
            "category": "sales",
            "location": "Dubai, UAE",
            "job_type": "part_time",
            "work_mode": "onsite"
        }}
        
        Example 3 (NOT A JOB - Announcement):
        Raw: "Happy New Year everyone! Best wishes for 2025!"
        JSON: {{
            "is_job": false,
            "confidence": 95,
            "category": null,
            "location": null,
            "job_type": null,
            "work_mode": null
        }}
        
        Example 4 (NOT A JOB - Promotional Spam):
        Raw: "Get rich quick! Click here for amazing opportunities!"
        JSON: {{
            "is_job": false,
            "confidence": 85,
            "category": null,
            "location": null,
            "job_type": null,
            "work_mode": null
        }}
        
        Post Text to Analyze:
        ---
        {job_post.raw_text}
        ---
        
        Return ONLY valid JSON with these exact fields:
        {{
            "is_job": boolean,
            "confidence": integer (0-100),
            "category": string or null,
            "location": string or null,
            "job_type": string or null,
            "work_mode": string or null
        }}
        """

        try:
            result = gemini_client.generate_json(prompt)
            if not result:
                logger.warning(f"No response from AI for JobPost {job_post.id}")
                # Default to treating as job (backward compatible)
                job_post.is_job = True
                job_post.classification_confidence = None
                job_post.needs_metadata_extraction = True  # Mark for retry
                job_post.save()
                return True

            # Extract classification results
            is_job = result.get('is_job', True)  # Default to True if missing
            confidence = result.get('confidence', 50)  # Default to low confidence
            
            # Store classification results
            job_post.classification_confidence = confidence
            
            # Decision logic: Is this a job posting?
            if not is_job or confidence < cls.CLASSIFICATION_THRESHOLD:
                # NOT A JOB - Mark as non-job and exit early
                job_post.is_job = False
                job_post.save()
                logger.info(
                    f"JobPost {job_post.id} classified as NON-JOB "
                    f"(is_job={is_job}, confidence={confidence}%)"
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
                f"JobPost {job_post.id} classified as JOB "
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

