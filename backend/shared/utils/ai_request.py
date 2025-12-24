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
            self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Sends a prompt to Gemini and expects a JSON response.
        """
        if not self.api_key:
            return None

        try:
            # We use a structured prompt to encourage JSON output
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                )
            )
            
            if response.text:
                return json.loads(response.text)
            return None
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return None

gemini_client = GeminiClient()
