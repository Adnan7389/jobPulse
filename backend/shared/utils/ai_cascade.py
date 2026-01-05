import logging
from .ai_clients import GeminiClient, DeepSeekClient, HuggingFaceClient

logger = logging.getLogger(__name__)

class AICascade:
    """
    Manages the 3-tier fallback system for AI operations.
    Tier 1: Gemini (Google) - Fast, cheap, high quality.
    Tier 2: DeepSeek R1 (via OpenRouter) - Powerful fallback, respects rate limits.
    Tier 3: HuggingFace (Local/Heuristic) - Guaranteed response when APIs fail.
    """
    
    def __init__(self):
        self.tier1 = GeminiClient()
        self.tier2 = DeepSeekClient()
        self.tier3 = HuggingFaceClient()
    
    def classify_with_fallback(self, job_text: str) -> tuple[dict, str]:
        """
        Returns: (result_dict, tier_used)
        tier_used is one of: 'gemini', 'deepseek', 'huggingface'
        """
        # Tier 1: Gemini
        try:
            result = self.tier1.classify_and_extract(job_text)
            if result:
                return result, 'gemini'
        except Exception as e:
            logger.warning(f"Tier 1 (Gemini) failed: {e}")
        
        # Tier 2: DeepSeek
        try:
            logger.info("Falling back to Tier 2 (DeepSeek)...")
            result = self.tier2.classify_and_extract(job_text)
            if result:
                return result, 'deepseek'
        except Exception as e:
            logger.error(f"Tier 2 (DeepSeek) failed: {e}")
        
        # Tier 3: HuggingFace / Fallback
        logger.warning("Falling back to Tier 3 (HuggingFace/Heuristic)...")
        result = self.tier3.classify_and_extract(job_text)
        return result, 'huggingface'
    
    def match_with_fallback(self, user_profile: str, job_text: str) -> tuple[dict, str]:
        """
        Returns: (result_dict, tier_used)
        tier_used is one of: 'gemini', 'deepseek', 'huggingface'
        """
        # Tier 1: Gemini
        try:
            result = self.tier1.semantic_match(user_profile, job_text)
            if result:
                return result, 'gemini'
        except Exception as e:
            logger.warning(f"Tier 1 (Gemini) match failed: {e}")
        
        # Tier 2: DeepSeek
        try:
            logger.info("Falling back to Tier 2 (DeepSeek) for matching...")
            result = self.tier2.semantic_match(user_profile, job_text)
            if result:
                return result, 'deepseek'
        except Exception as e:
            logger.error(f"Tier 2 (DeepSeek) match failed: {e}")
            
        # Tier 3: HuggingFace / Fallback
        logger.warning("Falling back to Tier 3 (HuggingFace/Heuristic) for matching...")
        result = self.tier3.semantic_match(user_profile, job_text)
        return result, 'huggingface'
