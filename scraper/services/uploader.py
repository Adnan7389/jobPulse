import logging
import requests
import config

logger = logging.getLogger(__name__)

class Uploader:
    @staticmethod
    def fetch_channels():
        """Fetch target channels from the Backend API."""
        try:
            url = f"{config.BACKEND_URL}/api/channels/"
            logger.info(f"Fetching channels from {url}")
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch channels: {e}")
            return []

    @staticmethod
    def send_job_post(job_data):
        """Send scraped job post to the Backend API."""
        try:
            url = f"{config.BACKEND_URL}/api/job_posts/"
            response = requests.post(url, json=job_data)
            if response.status_code in [200, 201]:
                logger.info(f"Successfully sent message {job_data.get('message_id')} (Channel {job_data.get('channel_id')}) to backend.")
                return True
            else:
                logger.error(f"Failed to send job post: Status {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending job post: {e}")
            return False
