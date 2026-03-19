"""Configuration module for the Alter Ego application."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for the Alter Ego application."""
    
    def __init__(self):
        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.pushover_user = os.getenv("PUSHOVER_USER")
        self.pushover_token = os.getenv("PUSHOVER_TOKEN")
        
        # Application settings
        self.name = "Aayush Vijayvergiya"
        self.model_name = "gpt-4o-mini"
        
        # File paths
        self.project_root = Path(__file__).parent.parent.parent
        self.static_dir = self.project_root / "static"
        self.linkedin_pdf_path = self.static_dir / "AayushVijayvergiya_LinkedIn.pdf"
        self.summary_file_path = self.static_dir / "summary.txt"
        
        # Pushover API settings
        self.pushover_url = "https://api.pushover.net/1/messages.json"
        
        # Portfolio website configuration
        self.portfolio_url = os.getenv("PORTFOLIO_URL", "")
        self.portfolio_cache_duration = int(os.getenv("PORTFOLIO_CACHE_DURATION", "3600"))  # 1 hour default
        
        # Web scraping settings
        self.user_agent = os.getenv("USER_AGENT", 
                                   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "10"))
        
    
    def validate_config(self) -> bool:
        """Validate required configuration values."""
        if not self.openai_api_key:
            print("Missing required configuration: OPENAI_API_KEY")
            return False
        return True
    
    
    @property
    def has_portfolio_url(self) -> bool:
        """Check if portfolio URL is configured."""
        return bool(self.portfolio_url and self.portfolio_url.strip())
    
    @property
    def has_pushover_config(self) -> bool:
        """Check if Pushover configuration is available."""
        return bool(self.pushover_user and self.pushover_token)

config = Config()
