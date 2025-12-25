import logging
from django.db.models import Q
from typing import List
from ..models import JobPost
from apps.users.models import User
from apps.notifications.models import Notification
from shared.utils.ai_request import gemini_client

logger = logging.getLogger(__name__)

class MatchOrchestrator:
    MATCH_THRESHOLD = 75

    @classmethod
    async def run(cls, job_post: JobPost):
        """
        Coordinates the matching process for a new job post.
        """
        # 1. SQL Pre-filtering
        candidates = cls.get_candidates(job_post)
        logger.info(f"Found {candidates.count()} candidates for JobPost {job_post.id} after pre-filtering")

        if not candidates.exists():
            return

        # 2. Iterative Semantic Matching
        for user in candidates:
            score, reasoning = await cls.get_semantic_match(user, job_post)
            
            if score >= cls.MATCH_THRESHOLD:
                # 3. Create Notification
                Notification.objects.create(
                    user=user,
                    job=job_post,
                    match_score=score,
                    reasoning=reasoning,
                    source='gemini'
                )
                logger.info(f"Created notification for User {user.id} on JobPost {job_post.id} (Score: {score})")

    @classmethod
    def get_candidates(cls, job_post: JobPost):
        """
        Efficient SQL filtering starting with channel subscription, 
        then matching Category, Location, Mode, and Type.
        """
        # 1. Start with users subscribed to this specific channel
        queryset = User.objects.filter(subscribed_channels=job_post.channel)

        # 2. Build preferences query
        query = Q(preferred_category=job_post.category)

        # Missing Data & "ALL" Preference Rules for Location
        if job_post.location:
            query &= Q(preferred_location=job_post.location) | Q(preferred_location__isnull=True) | Q(preferred_location='')

        # Missing Data & "ALL" Preference Rules for Mode
        if job_post.work_mode:
            query &= Q(preferred_mode=job_post.work_mode) | Q(preferred_mode='all')

        # Missing Data & "ALL" Preference Rules for Job Type
        if job_post.job_type:
            query &= Q(preferred_type=job_post.job_type) | Q(preferred_type='all')

        # 3. Apply preferences and return distinct users
        return queryset.filter(query).distinct()

    @classmethod
    async def get_semantic_match(cls, user: User, job_post: JobPost) -> tuple[int, str]:
        """
        Calls Gemini to get a semantic match score and reasoning.
        """
        prompt = f"""
        Perform a Semantic Fit Analysis between the following User Profile and Job Posting.
        
        User Profile:
        - Bio: {user.bio}
        - Skills: {user.skills}
        - Job Titles: {user.job_titles}
        - Experience Level: {user.experience_level} ({user.years_experience} years)

        Job Posting:
        - Title: {job_post.channel.name} (Source)
        - Content: {job_post.raw_text}

        Return ONLY a JSON object with:
        - score: An integer from 0 to 100
        - reasoning: A brief string explaining why it matches or doesn't match.
        """

        try:
            result = await gemini_client.generate_json(prompt)
            if result:
                return int(result.get('score', 0)), result.get('reasoning', '')
        except Exception as e:
            logger.error(f"Semantic matching failed for User {user.id}: {e}")
        
        return 0, "Error during matching"
