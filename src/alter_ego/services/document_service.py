"""Document processing services for the Alter Ego application."""

import time
from pathlib import Path
from typing import Optional, Dict, Any
import json

import httpx
from bs4 import BeautifulSoup
import html2text
from pypdf import PdfReader

from ..config import config
from ..utils.logger import logger


class DocumentService:
    """Service for loading and processing documents and web content asynchronously."""
    
    def __init__(self):
        self._linkedin_content: Optional[str] = None
        self._summary_content: Optional[str] = None
        self._portfolio_content: Optional[str] = None
        self._portfolio_cache: Dict[str, Any] = {}
        self._cache_file = config.static_dir / "portfolio_cache.json"
    
    async def get_linkedin_content(self) -> str:
        """Load and return LinkedIn PDF content."""
        if self._linkedin_content is None:
            self._linkedin_content = self._load_pdf_content(config.linkedin_pdf_path)
        return self._linkedin_content
    
    async def get_summary_content(self) -> str:
        """Load and return summary content."""
        if self._summary_content is None:
            self._summary_content = self._load_text_content(config.summary_file_path)
        return self._summary_content
    
    async def get_portfolio_content(self) -> str:
        """Load and return portfolio website content asynchronously."""
        if self._portfolio_content is None:
            self._portfolio_content = await self._load_portfolio_content()
        return self._portfolio_content
    
    async def get_combined_profile(self) -> str:
        """Get combined profile from LinkedIn, summary, and portfolio asynchronously."""
        sections = []
        
        # LinkedIn Profile
        linkedin = await self.get_linkedin_content()
        if linkedin and linkedin != "LinkedIn profile content not available.":
            sections.append("=== LINKEDIN PROFILE ===\n" + linkedin)
        
        # Summary
        summary = await self.get_summary_content() 
        if summary and summary != "Summary content not available.":
            sections.append("=== PROFESSIONAL SUMMARY ===\n" + summary)
        
        # Portfolio Website
        if config.has_portfolio_url:
            portfolio = await self.get_portfolio_content()
            if portfolio and portfolio != "Portfolio content not available.":
                sections.append("=== PORTFOLIO WEBSITE ===\n" + portfolio)
        
        if not sections:
            return "No profile information available."
        
        return "\n\n".join(sections)
    
    async def refresh_portfolio_content(self) -> str:
        """Force refresh of portfolio content from website asynchronously."""
        self._portfolio_content = None
        self._portfolio_cache = {}
        if self._cache_file.exists():
            self._cache_file.unlink()
        return await self.get_portfolio_content()
    
    async def _load_portfolio_content(self) -> str:
        """Load content from portfolio website with caching asynchronously."""
        if not config.has_portfolio_url:
            return "Portfolio URL not configured."
        
        try:
            # Check cache first
            cached_content = self._get_cached_portfolio()
            if cached_content:
                logger.info("Using cached portfolio content")
                return cached_content
            
            logger.info(f"Fetching portfolio content from: {config.portfolio_url}")
            
            # Scrape website
            content = await self._scrape_website(config.portfolio_url)
            
            # Cache the content
            self._cache_portfolio(content)
            
            return content
            
        except Exception as e:
            logger.error(f"Error loading portfolio content: {e}")
            
            # Try to return cached content even if expired
            if self._portfolio_cache.get('content'):
                logger.info("Returning expired cached content as fallback")
                return self._portfolio_cache['content']
            
            return "Portfolio content not available."
    
    async def _scrape_website(self, url: str) -> str:
        """Scrape content from a website asynchronously."""
        headers = {
            'User-Agent': config.user_agent,
        }
        
        try:
            async with httpx.AsyncClient(headers=headers, timeout=config.request_timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Convert to markdown-like text
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.body_width = 0  # Don't wrap lines
            
            # Get main content
            main_content = soup.find('main') or soup.find('body') or soup
            text_content = h.handle(str(main_content))
            
            # Clean up the content
            lines = text_content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):  # Keep content, remove excessive headers
                    cleaned_lines.append(line)
            
            content = '\n'.join(cleaned_lines)
            
            # Limit content length to avoid token limits
            if len(content) > 8000:  # Roughly 2000 tokens
                content = content[:8000] + "\n\n[Content truncated for length]"
            
            return content
            
        except httpx.HTTPError as e:
            logger.error(f"Request error while scraping {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing content from {url}: {e}")
            raise
    
    def _get_cached_portfolio(self) -> Optional[str]:
        """Get cached portfolio content if still valid."""
        try:
            if not self._cache_file.exists():
                return None
            
            with open(self._cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is still valid
            cache_time = cache_data.get('timestamp', 0)
            current_time = time.time()
            
            if current_time - cache_time < config.portfolio_cache_duration:
                self._portfolio_cache = cache_data
                return cache_data.get('content')
            
            return None
            
        except Exception as e:
            logger.error(f"Error reading portfolio cache: {e}")
            return None
    
    def _cache_portfolio(self, content: str) -> None:
        """Cache portfolio content to file."""
        try:
            cache_data = {
                'content': content,
                'timestamp': time.time(),
                'url': config.portfolio_url
            }
            
            # Ensure static directory exists
            config.static_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self._cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            self._portfolio_cache = cache_data
            logger.info("Portfolio content cached successfully")
            
        except Exception as e:
            logger.error(f"Error caching portfolio content: {e}")
    
    def _load_pdf_content(self, pdf_path: Path) -> str:
        """Load content from a PDF file."""
        try:
            if not pdf_path.exists():
                logger.warning(f"PDF file not found at {pdf_path}")
                # Try to load placeholder file instead
                placeholder_path = pdf_path.parent / "linkedin_placeholder.txt"
                if placeholder_path.exists():
                    logger.info(f"Loading placeholder content from {placeholder_path}")
                    return self._load_text_content(placeholder_path)
                return "LinkedIn profile content not available."
            
            reader = PdfReader(str(pdf_path))
            content = ""
            
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    content += text
            
            return content if content else "No content extracted from LinkedIn PDF."
            
        except Exception as e:
            logger.error(f"Error loading PDF content: {e}")
            # Try placeholder as fallback
            placeholder_path = pdf_path.parent / "linkedin_placeholder.txt"
            if placeholder_path.exists():
                logger.info(f"Loading placeholder content as fallback from {placeholder_path}")
                return self._load_text_content(placeholder_path)
            return "Error loading LinkedIn profile content."
    
    def _load_text_content(self, text_path: Path) -> str:
        """Load content from a text file."""
        try:
            if not text_path.exists():
                logger.warning(f"Text file not found at {text_path}")
                return "Summary content not available."
            
            with open(text_path, "r", encoding="utf-8") as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Error loading text content: {e}")
            return "Error loading summary content."
