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
    def get_semantic_match(cls, user: User, job_post: JobPost) -> tuple[int, str, str]:
        """
        Calls AI Cascade to get a semantic match score and reasoning (Synchronous).
        Returns: (score, reasoning, match_source)
        """
        from shared.utils.ai_cascade import AICascade
        
        cascade = AICascade()
        
        # Construct profile string first to avoid repeated DB hits or string formatting
        user_profile_text = (
            f"Bio: {user.bio}\n"
            f"Skills: {user.skills}\n"
            f"Job Titles: {user.job_titles}\n"
            f"Experience Level: {user.experience_level} ({user.years_experience} years)"
        )

        try:
            result, tier_used = cascade.match_with_fallback(user_profile_text, job_post.raw_text)
            if result:
                return (
                    int(result.get('score', 0)), 
                    result.get('reasoning', ''), 
                    tier_used
                )
        except Exception as e:
            logger.error(f"Semantic matching failed for User {user.id}: {e}")
        
        return 0, "Error during matching", "error"
