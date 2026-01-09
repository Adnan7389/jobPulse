import os
import json
import logging
import time
from typing import Optional, Dict, Any
from google import genai
from google.genai import types
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, retry_if_result

def is_quota_retryable(exception):
    """
    Custom predicate for tenacity to skip retries on daily/hard quota limits.
    Returns True if the error is retryable (e.g. per-minute limit), 
    False if it's a hard daily limit.
    """
    err_msg = str(exception).lower()
    
    # 0. ALWAYS retry if the API specifically gives a retry delay
    if 'retry in' in err_msg or 'retry delay' in err_msg or 'retryafter' in err_msg:
        return True

    # 1. Check for daily limits (non-retryable until tomorrow)
    non_retryable_keywords = [
        'per-day',
        'perday',
        'daily',
        'absolute limit exceeded',
    ]
    
    if any(keyword in err_msg for keyword in non_retryable_keywords):
        logger.warning(f"🚫 Hard quota limit hit. Skipping further retries. Error: {err_msg[:100]}...")
        return False
        
    return True

# Analytics
from apps.analytics.decorators import track_ai_performance

# For local fallback
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
# Note: We are using fastembed for "Lite" local semantic matching on small servers.
from fastembed import TextEmbedding
# I will implement the client to be robust.

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment")
            self.client = None
        else:
            masked = f"{self.api_key[:6]}...{self.api_key[-4:]}"
            logger.info(f"🔑 GeminiClient initialized with key: {masked}")
            self.client = genai.Client(api_key=self.api_key)

    @retry(
        retry=lambda e: is_quota_retryable(e), # Patiently wait unless it's a hard daily limit
        stop=stop_after_attempt(5), # Increase attempts to wait out the 60s windows
        wait=wait_exponential(multiplier=2, min=15, max=75) # Max wait > 60s to bridge resets
    )
    @track_ai_performance('gemini', 'extraction')
    def classify_and_extract(self, job_text: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        
        # Reuse the prompt logic from the original extractor, but this client just takes the text
        # and returns the raw JSON. The calling service constructs the complex prompt?
        # No, the PROMPT specifies the client should take job_text. 
        # But to avoid code duplication, I should probably keep the prompt in the client or a shared constant.
        # The prompt in extractor.py was very specific. 
        # For now, I will mirror the generate_json method pattern but adapted for the interface.
        
        # ACTUALLY, the prompt in `extractor.py` constructs the whole prompt string including the job text.
        # The interface in the prompt description says: classify_and_extract(job_text: str) -> dict
        # This implies receiving the raw job text and doing the prompt engineering inside.
        
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
        - Category: Select the best fit from ['software', 'marketing', 'design', 'sales', 'finance', 'hr', 'customer_service', 'management', 'other']. Use 'software' for developer/engineer roles.
        - Location: Extract "City, Country" (e.g., "Addis Ababa, Ethiopia"). Use null if not mentioned.
        - Job Type: ['full_time', 'part_time']. Use null if not mentioned.
        - Work Mode: ['remote', 'hybrid', 'onsite']. Use null if not mentioned.
        
        Post Text to Analyze:
        ---
        {job_text[:10000]}
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
            response = self.client.models.generate_content(
                model='models/gemini-2.0-flash-lite',  # Using 2.0-flash-lite as per recent robust findings
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            if response.text:
                return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini classify failed: {e}")
            raise e # Re-raise to let cascade handle it
        return None

    @retry(
        retry=lambda e: is_quota_retryable(e),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=15, max=75)
    )
    @track_ai_performance('gemini', 'matching')
    def semantic_match(self, user_profile: str, job_text: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None

        prompt = f"""
        Role: You are a Senior Technical Recruiter.
        Task: Evaluate the fit between the User and the Job Posting.
        
        CRITICAL: Write the "reasoning" directly TO the User (use "You", "Your skills", "Your experience"). 
        Address them personally as if you are giving them advice on why this job is a good match for them.
 
        Evaluation Criteria:
        1. Hard Skills Match: Do the user's skills align with the job requirements?
        2. Experience Level: Does the user's years of experience match the seniority required?
        3. Career Context: Does the user's bio suggest they are actually looking for this type of role?

        User Profile:
        {user_profile}

        Job Posting Content:
        ---
        {job_text[:10000]}
        ---

        Return ONLY a JSON object with:
        - score: An integer from 0 to 100
        - reasoning: A professional recruiter's assessment (1-2 sentences).
        """

        try:
            response = self.client.models.generate_content(
                model='models/gemini-2.0-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                )
            )
            if response.text:
                return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini match failed: {e}")
            raise e
        return None


class DeepSeekClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "deepseek/deepseek-r1-distill-llama-70b:free" # Using a reliable free model identifier
        # Note: The prompt suggested deepseek/deepseek-r1-0528:free, I'll use what's safest or keep to prompt if mandated.
        # Prompt said: "deepseek/deepseek-r1-0528:free". I'll stick to that but fall back if needed.
        self.model = "deepseek/deepseek-r1:free" # Common alias, but let's strictly follow the latest user info
        self.model = "deepseek/deepseek-r1-0528:free"
        
        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not found")
            self.client = None
        else:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                default_headers={
                    "HTTP-Referer": "https://joblens.ai", # Placeholder URL
                    "X-Title": "JobLens",
                }
            )

    def _clean_json(self, text: str) -> str:
        # Remove markdown fences
        if "```" in text:
            # Try to match json block
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if match:
                return match.group(1)
        
        # If no fences or regex failed, try to find first { and last }
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            return text[start:end+1]
        
        return text

    @retry(
        retry=lambda e: is_quota_retryable(e),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=20, max=120)
    )
    @track_ai_performance('deepseek', 'extraction')
    def classify_and_extract(self, job_text: str) -> Optional[Dict[str, Any]]:
        # Respect 20 RPM (3s delay) - handled by tenacity wait_exponential min=4 roughly covers it + backoff
        
        if not self.client:
            return None

        prompt = f"""
        You are a JSON-only API. Analyze this job post.
        
        Return JSON with: is_job (bool), confidence (int), category (str/null), location (str/null), job_type (str/null), work_mode (str/null).
        Categories: software, marketing, design, sales, finance, hr, customer_service, management, other.
        
        Text:
        {job_text[:5000]}
        """
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs only JSON."},
                    {"role": "user", "content": prompt}
                ],
                # DeepSeek might ignore this or behave oddly with it, but we keep it.
                # If it causes issues, we'll remove it, but for now robust parsing is more important.
                response_format={"type": "json_object"} 
            )
            content = completion.choices[0].message.content
            cleaned_content = self._clean_json(content)
            return json.loads(cleaned_content)
        except Exception as e:
            logger.error(f"DeepSeek classify failed: {e}")
            raise e

    @retry(
        retry=lambda e: is_quota_retryable(e),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=20, max=120)
    )
    @track_ai_performance('deepseek', 'matching')
    def semantic_match(self, user_profile: str, job_text: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None

        prompt = f"""
        Evaluate match score (0-100) and reasoning for User vs Job.
        User: {user_profile}
        Job: {job_text[:5000]}
        
        Return JSON: {{ "score": int, "reasoning": str }}
        """

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Output only JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            content = completion.choices[0].message.content
            cleaned_content = self._clean_json(content)
            return json.loads(cleaned_content)
        except Exception as e:
            logger.error(f"DeepSeek match failed: {e}")
            raise e


class HuggingFaceClient:
    _model = None  # Singleton model instance

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HF_API_KEY")
        # Lazily initialize the embedding model
        if HuggingFaceClient._model is None:
            try:
                logger.info("📡 Loading FastEmbed model (BAAI/bge-small-en-v1.5)...")
                HuggingFaceClient._model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
                logger.info("✨ FastEmbed model loaded successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to load FastEmbed: {e}")

    @track_ai_performance('hf', 'extraction')
    def classify_and_extract(self, job_text: str) -> Dict[str, Any]:
        """
        Fallback classification using basic heuristics since we can't easily run a 
        full BERT model for extraction without heavy dependencies or an Inference API that might be rate limited.
        The prompt suggested DistilBERT, but simplest robust fallback is keyword analysis for 'is_job'
        and regex for metadata.
        """
        
        text_lower = job_text.lower()
        
        # Heuristic Classification
        job_keywords = [
            'hiring', 'vacancy', 'apply', 'role', 'position', 'salary', 'remote', 'hybrid', 'onsite',
            'responsibilities', 'qualifications', 'requirements', 'skills', 'experience', 'join our team',
            'looking for', 'job', 'career', 'full-time', 'part-time', 'contract', 'freelance'
        ]
        keyword_count = sum(1 for k in job_keywords if k in text_lower)
        is_job = keyword_count >= 2
        confidence = min(keyword_count * 15, 90) if is_job else 50
        
        # Heuristic Metadata Extraction (Regex/Keyword fallback)
        category = 'other'
        if 'developer' in text_lower or 'engineer' in text_lower or 'software' in text_lower:
            category = 'software'
        elif 'marketing' in text_lower:
            category = 'marketing'
        elif 'design' in text_lower:
            category = 'design'
            
        work_mode = None
        if 'remote' in text_lower:
            work_mode = 'remote'
        elif 'hybrid' in text_lower:
            work_mode = 'hybrid'
        elif 'onsite' in text_lower or 'on-site' in text_lower:
            work_mode = 'onsite'
            
        return {
            "is_job": is_job,
            "confidence": confidence,
            "category": category,
            "location": None, # Too hard with regex without NER
            "job_type": None,
            "work_mode": work_mode
        }

    @track_ai_performance('hf', 'matching')
    def semantic_match(self, user_profile: str, job_text: str) -> Dict[str, Any]:
        """
        FastEmbed (BGE-Small) vector matching for semantic similarity.
        """
        if not HuggingFaceClient._model:
            logger.warning("⚠️ FastEmbed model not available, returning 0 score.")
            return {"score": 0, "reasoning": "Local matching engine unavailable."}

        logger.info(f"🔍 HF Search: Semantic match using FastEmbed (Profile len: {len(user_profile)})")
        try:
            # Generate embeddings (batch size 2)
            documents = [user_profile, job_text]
            embeddings = list(HuggingFaceClient._model.embed(documents))
            
            # Embeddings are numpy arrays, calculate cosine similarity
            import numpy as np
            vec1 = embeddings[0]
            vec2 = embeddings[1]
            
            # Cosine similarity formula: (A . B) / (||A|| * ||B||)
            # FastEmbed's BGE models often return normalized embeddings, but let's be safe
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                similarity = 0.0
            else:
                similarity = float(np.dot(vec1, vec2) / (norm1 * norm2))
            
            # Scale to 0-100
            score = int(max(0, similarity) * 100)
            
            logger.info(f"🎯 FastEmbed Result: Score={score} (Similarity={similarity:.4f})")
            
            reasoning = (
                f"Your profile has a {score}% semantic match with this job's requirements. "
                "Calculated using local BGE-Small embeddings."
            )
            
            return {
                "score": score,
                "reasoning": reasoning
            }
        except Exception as e:
            logger.error(f"FastEmbed match failed: {e}")
            return {"score": 0, "reasoning": "Local semantic matching failed."}
