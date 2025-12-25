import google.generativeai as genai
import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment")
        else:
            genai.configure(api_key=self.api_key)
            # Use gemini-3-flash-preview as it is available in this environment
            self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Sends a prompt to Gemini and expects a JSON response (Synchronous).
        Includes resilience: Hard timeouts, Low Temperature, and Error handling.
        """
        if not self.api_key:
            return None

        # Part 5: Controlled truncation (Ensure prompt isn't excessively long)
        # 10k chars is plenty for job posts while staying safe
        safe_prompt = prompt[:10000]

        try:
            # Use gemini-3-flash-preview for performance and availability
            model = genai.GenerativeModel('gemini-3-flash-preview')
            
            # Part 5: Low Temperature for Judgment > Imagination
            # Part 4: Hard time limit (timeout=30)
            response = model.generate_content(
                safe_prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1,  # Stable, repeatable results
                ),
                request_options={"timeout": 30}  # Prevent hanging workers
            )
            
            if response.text:
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    logger.error("AI returned invalid JSON")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return None

gemini_client = GeminiClient()
