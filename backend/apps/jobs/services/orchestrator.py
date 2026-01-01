import logging
from django.db.models import Q
from asgiref.sync import sync_to_async
from typing import List
from ..models import JobPost
from apps.users.models import User
from apps.notifications.models import Notification
from apps.notifications.tasks import send_notification_to_user
from shared.utils.ai_request import gemini_client

logger = logging.getLogger(__name__)

class MatchOrchestrator:
    MATCH_THRESHOLD = 75

    @classmethod
    def run(cls, job_post: JobPost):
        """
        Coordinates the matching process for a new job post (Synchronous).
        """
        # Defense-in-depth: Verify this is actually a job post
        # This should already be filtered in the task, but we double-check
        if not job_post.is_job:
            logger.warning(
                f"Orchestrator called on non-job post {job_post.id}. "
                f"This should have been filtered earlier. Skipping."
            )
            return
        
        # 1. SQL Pre-filtering
        candidates = cls.get_candidates(job_post)
        logger.info(f"Found {len(candidates)} candidates for JobPost {job_post.id} after pre-filtering")

        if not candidates:
            return

        # 2. Iterative Semantic Matching (Throttled via Celery)
        from apps.jobs.tasks import process_semantic_match
        
        for user in candidates:
            # Move individual matching to its own rate-limited task
            process_semantic_match.delay(user.id, job_post.id)
            logger.info(f"Queued semantic match task for User {user.id} on JobPost {job_post.id}")

    @classmethod
    def get_candidates(cls, job_post: JobPost):
        """
        Efficient SQL filtering (Synchronous).
        Supports Graceful Degradation: If AI fields are missing, falls back to keyword matching.
        """
        # 1. Start with users subscribed to this specific channel
        queryset = User.objects.filter(subscribed_channels=job_post.channel)

        # 2. Build preferences query
        if job_post.category:
            # AI Path: Target accurate categorization
            query = Q(preferred_category=job_post.category)
        else:
            # Part 4: Graceful Degradation Path (AI Failed to set category)
            # Fallback to a broader keyword search in raw_text
            logger.warning(f"JobPost {job_post.id} missing category. Falling back to keyword match.")
            query = Q()
            # Note: In a real production system, we might search user.skills or user.job_titles here
            # For MVP fallback, we'll just allow all subscribed users to be processed by semantic matching
            # if the categorical filter failed, as semantic matching is more robust.
            pass

        # Missing Data & "ALL" Preference Rules for Location
        if job_post.location:
            query &= Q(preferred_location=job_post.location) | Q(preferred_location__isnull=True) | Q(preferred_location='')

        # Missing Data & "ALL" Preference Rules for Mode
        if job_post.work_mode:
            query &= Q(preferred_mode=job_post.work_mode) | Q(preferred_mode='all')

        # Missing Data & "ALL" Preference Rules for Job Type
        if job_post.job_type:
            query &= Q(preferred_type=job_post.job_type) | Q(preferred_type='all')

        # 3. Apply preferences and return distinct users list
        return list(queryset.filter(query).distinct())

    @classmethod
    def get_semantic_match(cls, user: User, job_post: JobPost) -> tuple[int, str]:
        """
        Calls Gemini to get a semantic match score and reasoning (Synchronous).
        """
        prompt = f"""
        Role: You are a Senior Technical Recruiter.
        Task: Evaluate the fit between the User and the Job Posting.
        
        CRITICAL: Write the "reasoning" directly TO the User (use "You", "Your skills", "Your experience"). 
        Address them personally as if you are giving them advice on why this job is a good match for them.

        Evaluation Criteria:
        1. Hard Skills Match: Do the user's skills align with the job requirements?
        2. Experience Level: Does the user's years of experience match the seniority required?
        3. Career Context: Does the user's bio suggest they are actually looking for this type of role?
        
        Example 1 (Perfect Match):
        User: Python, Django, 5 years exp.
        Job: Senior Python Developer, Django required.
        Score: 95
        Reasoning: "You are an excellent fit for this role as your 5 years of Django experience perfectly align with the senior requirements."
        
        Example 2 (Poor Match):
        User: Junior Designer, 1 year exp.
        Job: Project Manager, 10 years exp.
        Score: 10
        Reasoning: "This role requires significantly more management experience than you currently possess, and the field differs from your design background."

        User Profile:
        - Bio: {user.bio}
        - Skills: {user.skills}
        - Job Titles: {user.job_titles}
        - Experience Level: {user.experience_level} ({user.years_experience} years)

        Job Posting Content:
        ---
        {job_post.raw_text}
        ---

        Return ONLY a JSON object with:
        - score: An integer from 0 to 100
        - reasoning: A professional recruiter's assessment (1-2 sentences).
        """

        try:
            result = gemini_client.generate_json(prompt)
            if result:
                return int(result.get('score', 0)), result.get('reasoning', '')
        except Exception as e:
            logger.error(f"Semantic matching failed for User {user.id}: {e}")
        
        return 0, "Error during matching"
