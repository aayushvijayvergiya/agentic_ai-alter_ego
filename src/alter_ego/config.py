"""Configuration module for the Alter Ego application."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from .utils.logger import logger

load_dotenv()

class Config:
    """Configuration class for the Alter Ego application."""
    
    def __init__(self):
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")

        # SMTP Configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.notification_email = os.getenv("NOTIFICATION_EMAIL")

        # Application settings
        self.name = "Aayush Vijayvergiya"
        self.model_name = os.getenv("MODEL_NAME", "openai/gpt-oss-120b:free")
        self.openrouter_base_url = "https://openrouter.ai/api/v1"
        self.portfolio_domain = os.getenv("PORTFOLIO_DOMAIN")
        self.max_messages_per_session = int(os.getenv("MAX_MESSAGES_PER_SESSION", "20"))
        
        # File paths
        self.project_root = Path(__file__).parent.parent.parent
        self.static_dir = self.project_root / "static"
        self.linkedin_pdf_path = self.static_dir / "AayushVijayvergiya_LinkedIn.pdf"
        self.summary_file_path = self.static_dir / "summary.md"
        
        # Pushover API settings
        self.pushover_url = "https://api.pushover.net/1/messages.json"
        
        # Portfolio website configuration
        self.portfolio_url = os.getenv("PORTFOLIO_URL", "")
        self.portfolio_cache_duration = int(os.getenv("PORTFOLIO_CACHE_DURATION", "3600"))  # 1 hour default
        
        # Web scraping settings
        self.user_agent = os.getenv("USER_AGENT", 
                                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "10"))

        # GitHub configuration
        self.github_username = os.getenv("GITHUB_USERNAME", "aayushvijayvergiya")
        self.github_token: Optional[str] = os.getenv("GITHUB_TOKEN")
        self.github_cache_duration = int(os.getenv("GITHUB_CACHE_DURATION", "3600"))
        
    
    def validate_config(self) -> bool:
        """Validate required configuration values."""
        if not self.openrouter_api_key and not self.openai_api_key:
            logger.error("Missing required configuration: OPENROUTER_API_KEY (or OPENAI_API_KEY)")
            return False
        return True

    @property
    def active_api_key(self) -> Optional[str]:
        """Return the active API key — OpenRouter takes priority."""
        return self.openrouter_api_key or self.openai_api_key

    @property
    def use_openrouter(self) -> bool:
        """Return True if OpenRouter is configured."""
        return bool(self.openrouter_api_key)
    
    
    @property
    def has_portfolio_url(self) -> bool:
        """Check if portfolio URL is configured."""
        return bool(self.portfolio_url and self.portfolio_url.strip())
    
    @property
    def has_pushover_config(self) -> bool:
        """Check if Pushover configuration is available."""
        return bool(self.pushover_user and self.pushover_token)

    @property
    def has_smtp_config(self) -> bool:
        """Check if SMTP configuration is available."""
        return bool(self.smtp_host and self.smtp_port and self.smtp_user and self.smtp_password and self.notification_email)

config = Config()
