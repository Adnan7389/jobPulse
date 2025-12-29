import httpx
import asyncio
import logging
import re
from typing import Dict, Any, Tuple, Optional, List

from config import config

logger = logging.getLogger(__name__)

class BackendAPIError(Exception):
    """Custom exception for backend API errors"""
    pass


def normalize_channel_username(channel_input: str) -> str:
    """
    Normalize channel username from various input formats.
    
    Accepts:
    - @ethiojobs
    - https://t.me/ethiojobs
    - t.me/ethiojobs
    - ethiojobs
    
    Returns: ethiojobs (without @)
    """
    channel_input = channel_input.strip()
    
    # Remove URL patterns
    channel_input = re.sub(r'^https?://', '', channel_input)
    channel_input = re.sub(r'^t\.me/', '', channel_input)
    
    # Remove @ prefix
    channel_input = channel_input.lstrip('@')
    
    # Remove any trailing slashes or query params
    channel_input = channel_input.split('/')[0].split('?')[0]
    
    return channel_input.lower()

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
    
    # Use configuration
    max_retries = config.max_retries
    base_delay = config.retry_delay
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=float(config.api_timeout)) as client:
                response = await client.post(url, json=user_data)
                
                if response.status_code in [200, 201]:
                    logger.info(f"Successfully created/updated user profile for telegram_id={user_data.get('telegram_id')}")
                    return True, "Profile saved successfully! 🎉"
                
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
                    return False, f"Unexpected error ({response.status_code}). Please try again later."
        
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
            return False, f"Unexpected error: {str(e)[:50]}"
    
    return False, "Failed to create profile after multiple attempts. Please try again later."


async def get_user_profile(telegram_id: int) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Fetch user profile from Django backend by telegram_id
    
    Args:
        telegram_id: Telegram user ID
    
    Returns:
        Tuple of (success: bool, data: dict | None, message: str)
    """
    url = f"{config.backend_url}/api/users/?telegram_id={telegram_id}"
    
    try:
        async with httpx.AsyncClient(timeout=float(config.api_timeout)) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                # API returns a list, get first result
                if data and len(data) > 0:
                    logger.info(f"Successfully fetched profile for telegram_id={telegram_id}")
                    return True, data[0], "Profile fetched successfully"
                else:
                    logger.warning(f"No profile found for telegram_id={telegram_id}")
                    return False, None, "Profile not found"
            
            elif response.status_code == 404:
                return False, None, "Profile not found"
            
            else:
                logger.error(f"Unexpected status code {response.status_code}: {response.text}")
                return False, None, "Failed to fetch profile"
    
    except httpx.ConnectError:
        logger.error("Connection error while fetching profile")
        return False, None, "Unable to connect to server"
    
    except httpx.TimeoutException:
        logger.error("Timeout while fetching profile")
        return False, None, "Server timeout"
    
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False, None, "An unexpected error occurred"


async def update_user_profile(telegram_id: int, update_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Update user profile in Django backend
    
    Args:
        telegram_id: Telegram user ID
        update_data: Dictionary with fields to update
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # First, fetch the user to get their ID
    success, user_data, message = await get_user_profile(telegram_id)
    
    if not success:
        return False, "User not found. Please complete onboarding first with /start"
    
    user_id = user_data.get('id')
    url = f"{config.backend_url}/api/users/{user_id}/"
    
    try:
        async with httpx.AsyncClient(timeout=float(config.api_timeout)) as client:
            response = await client.patch(url, json=update_data)
            
            if response.status_code == 200:
                logger.info(f"Successfully updated profile for telegram_id={telegram_id}")
                return True, "Profile updated successfully! 🎉"
            
            elif response.status_code == 400:
                error_data = response.json()
                logger.warning(f"Validation error: {error_data}")
                return False, "Some information was invalid. Please try again."
            
            else:
                logger.error(f"Unexpected status code {response.status_code}: {response.text}")
                return False, "Failed to update profile"
    
    except (httpx.ConnectError, httpx.TimeoutException):
        logger.error("Network error while updating profile")
        return False, "Unable to connect to server. Please try again later."
    
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False, "An unexpected error occurred"


async def add_channel(channel_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
    """
    Add a channel to monitor in Django backend
    
    Args:
        channel_data: Dictionary with keys: name, channel_username, channel_id, added_by (user_id)
    
    Returns:
        Tuple of (success: bool, message: str, channel_id: int | None)
    """
    url = f"{config.backend_url}/api/channels/"
    
    max_retries = config.max_retries
    base_delay = config.retry_delay
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=float(config.api_timeout)) as client:
                response = await client.post(url, json=channel_data)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    channel_id = data.get('id')
                    logger.info(f"Successfully added channel: {channel_data.get('channel_username')}")
                    return True, f"Channel @{channel_data.get('channel_username')} added successfully! 🎉", channel_id
                
                elif response.status_code == 400:
                    error_data = response.json()
                    logger.warning(f"Channel validation error: {error_data}")
                    
                    # Check for duplicate channel_username
                    if 'channel_username' in error_data:
                        return False, "This channel is already being monitored!", None
                    
                    return False, "Invalid channel data. Please check the channel name.", None
                
                else:
                    logger.error(f"Unexpected status code {response.status_code}: {response.text}")
                    return False, "Failed to add channel", None
        
        except httpx.ConnectError:
            logger.error(f"Connection error on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            else:
                return False, "Unable to connect to server. Please try again later.", None
        
        except httpx.TimeoutException:
            logger.error(f"Timeout on attempt {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                continue
            else:
                return False, "Server timeout. Please try again later.", None
        
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return False, "An unexpected error occurred", None
    
    return False, "Failed to add channel after multiple attempts", None


async def get_user_channels(user_id: int) -> Tuple[bool, Optional[List[Dict]], str]:
    """
    Get list of channels added by a user
    
    Args:
        user_id: User's database ID (not telegram_id)
    
    Returns:
        Tuple of (success: bool, channels: list | None, message: str)
    """
    url = f"{config.backend_url}/api/channels/?added_by={user_id}"
    
    try:
        async with httpx.AsyncClient(timeout=float(config.api_timeout)) as client:
            response = await client.get(url)
            
            if response.status_code == 200:
                channels = response.json()
                logger.info(f"Fetched {len(channels)} channels for user_id={user_id}")
                return True, channels, "Channels fetched successfully"
            
            else:
                logger.error(f"Unexpected status code {response.status_code}: {response.text}")
                return False, None, "Failed to fetch channels"
    
    except (httpx.ConnectError, httpx.TimeoutException):
        logger.error("Network error while fetching channels")
        return False, None, "Unable to connect to server"
    
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False, None, "An unexpected error occurred"


async def remove_channel(channel_id: int) -> Tuple[bool, str]:
    """
    Remove a channel from monitoring
    
    Args:
        channel_id: Channel's database ID
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    url = f"{config.backend_url}/api/channels/{channel_id}/"
    
    try:
        async with httpx.AsyncClient(timeout=float(config.api_timeout)) as client:
            response = await client.delete(url)
            
            if response.status_code == 204:
                logger.info(f"Successfully removed channel_id={channel_id}")
                return True, "Channel removed successfully! ✅"
            
            elif response.status_code == 404:
                return False, "Channel not found"
            
            else:
                logger.error(f"Unexpected status code {response.status_code}: {response.text}")
                return False, "Failed to remove channel"
    
    except (httpx.ConnectError, httpx.TimeoutException):
        logger.error("Network error while removing channel")
        return False, "Unable to connect to server"
    
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return False, "An unexpected error occurred"

