import httpx
import asyncio
import logging
from typing import Dict, Any, Tuple

from config import config

logger = logging.getLogger(__name__)

class BackendAPIError(Exception):
    """Custom exception for backend API errors"""
    pass

async def create_user_profile(user_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Create user profile in Django backend
    
    Args:
        user_data: Dictionary with keys: telegram_id, skills, job_titles, 
                   experience_level, years_experience, bio
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    url = f"{config.backend_url}/api/users/"
    
    # Retry configuration
    max_retries = 3
    base_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=user_data)
                
                if response.status_code == 201:
                    logger.info(f"Successfully created user profile for telegram_id={user_data.get('telegram_id')}")
                    return True, "Profile created successfully! 🎉"
                
                elif response.status_code == 400:
                    # User might already exist or validation error
                    error_data = response.json()
                    logger.warning(f"Backend validation error: {error_data}")
                    
                    # Check if it's a duplicate telegram_id error
                    if 'telegram_id' in error_data:
                        return False, "You already have a profile registered! Use /start to update your preferences."
                    
                    # Other validation errors
                    error_msg = "Some information was invalid. Please try again with /start"
                    return False, error_msg
                
                else:
                    logger.error(f"Unexpected status code {response.status_code}: {response.text}")
                    return False, "An unexpected error occurred. Please try again later."
        
        except httpx.ConnectError:
            logger.error(f"Connection error on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                # Exponential backoff
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            else:
                return False, "Unable to connect to the server. Please try again later."
        
        except httpx.TimeoutException:
            logger.error(f"Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            else:
                return False, "The server is taking too long to respond. Please try again later."
        
        except Exception as e:
            logger.exception(f"Unexpected error during API call: {e}")
            return False, "An unexpected error occurred. Please try again later."
    
    return False, "Failed to create profile after multiple attempts. Please try again later."
