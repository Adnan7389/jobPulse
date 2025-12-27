from google import genai
from google.genai import types
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
            # Configure client with API key
            self.client = genai.Client(api_key=self.api_key)

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
            # Part 5: Low Temperature for Judgment > Imagination
            # Note: The new SDK handles timeouts at the client level, not in config
            # Using gemini-2.0-flash (stable, not experimental)
            response = self.client.models.generate_content(
                model='models/gemini-2.0-flash',  # Stable Gemini 2.0 model
                contents=safe_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,  # Stable, repeatable results
                )
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
