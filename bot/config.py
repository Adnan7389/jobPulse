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
    
    def __post_init__(self):
        """Validate required configuration"""
        if not self.bot_token:
            raise ValueError("BOT_TOKEN environment variable is required")
        if not self.backend_url:
            raise ValueError("BACKEND_URL environment variable is required")

# Initialize configuration
config = Config(
    bot_token=os.getenv("BOT_TOKEN", ""),
    backend_url=os.getenv("BACKEND_URL", "http://web:8000")
)
