import logging
from django.db.models import Q
from asgiref.sync import sync_to_async
from typing import List
from ..models import JobPost
from apps.users.models import User
from apps.notifications.models import Notification
from shared.utils.ai_request import gemini_client

logger = logging.getLogger(__name__)

class MatchOrchestrator:
    MATCH_THRESHOLD = 75

    @classmethod
    def run(cls, job_post: JobPost):
        """
        Coordinates the matching process for a new job post (Synchronous).
        """
        # 1. SQL Pre-filtering
        candidates = cls.get_candidates(job_post)
        logger.info(f"Found {len(candidates)} candidates for JobPost {job_post.id} after pre-filtering")

        if not candidates:
            return

        # 2. Iterative Semantic Matching
        for user in candidates:
            score, reasoning = cls.get_semantic_match(user, job_post)
            logger.info(f"Semantic Match for User {user.id} on JobPost {job_post.id}: Score={score}")
            
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
            else:
                logger.info(f"Match score {score} below threshold {cls.MATCH_THRESHOLD} for User {user.id}")

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

        # 3. Apply preferences and return distinct users list
        return list(queryset.filter(query).distinct())

    @classmethod
    def get_semantic_match(cls, user: User, job_post: JobPost) -> tuple[int, str]:
        """
        Calls Gemini to get a semantic match score and reasoning (Synchronous).
        """
        prompt = f"""
        Role: You are a Senior Technical Recruiter with 10+ years of experience in talent acquisition.
        Task: Evaluate the "Semantic Fit Score" between the User Profile and the Job Posting provided below.
        
        Evaluation Criteria:
        1. Hard Skills Match: Do the user's skills align with the job requirements?
        2. Experience Level: Does the user's years of experience match the seniority required?
        3. Career Context: Does the user's bio suggest they are actually looking for this type of role?
        
        Example 1 (Perfect Match):
        User: Python, Django, 5 years exp.
        Job: Senior Python Developer, Django required.
        Score: 95
        Reasoning: "Excellent alignment in tech stack and experience level. The user is a direct fit for the senior requirements."
        
        Example 2 (Poor Match):
        User: Junior Designer, 1 year exp.
        Job: Project Manager, 10 years exp.
        Score: 10
        Reasoning: "Total mismatch in both role type and seniority. No relevant experience detected."

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
