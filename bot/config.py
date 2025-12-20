import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Bot configuration from environment variables"""
    bot_token: str
    backend_url: str
    api_timeout: int
    max_retries: int
    retry_delay: int
    enable_health_checks: bool
    
    def __post_init__(self):
        """Validate required configuration"""
        if not self.bot_token:
            raise ValueError("BOT_TOKEN environment variable is required")
        if not self.backend_url:
            raise ValueError("BACKEND_URL environment variable is required")

# Initialize configuration
config = Config(
    bot_token=os.getenv("BOT_TOKEN", ""),
    backend_url=os.getenv("BACKEND_URL", "http://web:8000"),
    api_timeout=int(os.getenv("API_TIMEOUT", "10")),
    max_retries=int(os.getenv("MAX_RETRIES", "3")),
    retry_delay=int(os.getenv("RETRY_DELAY", "1")),
    enable_health_checks=os.getenv("ENABLE_HEALTH_CHECKS", "true").lower() == "true"
)
