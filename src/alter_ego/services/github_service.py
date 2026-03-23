"""GitHub service for fetching public profile and repository data."""

import asyncio
import base64
import json
import time
from typing import Any, Dict, List, Optional

import httpx

from ..config import config
from ..utils.logger import logger


class GitHubService:
    """Service for fetching public GitHub profile and repository data asynchronously."""

    _REST_URL = "https://api.github.com"

    def __init__(self) -> None:
        self._github_content: Optional[str] = None
        self._cache_file = config.static_dir / "github_cache.json"
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": config.user_agent,
        }
        if config.github_token:
            self._headers["Authorization"] = f"Bearer {config.github_token}"

    async def get_github_content(self) -> str:
        """Return cached GitHub profile content, fetching if needed asynchronously."""
        if self._github_content is None:
            self._github_content = await self._load_github_content()
        return self._github_content

    async def _load_github_content(self) -> str:
        """Load GitHub content from cache or live API asynchronously."""
        cached = self._get_cached_content()
        if cached:
            logger.info("Using cached GitHub content")
            return cached

        logger.info(f"Fetching GitHub content for: {config.github_username}")
        try:
            content = await self._fetch_profile_content()
            self._cache_content(content)
            return content
        except Exception as e:
            logger.error(f"Error fetching GitHub content: {e}")
            if self._cache_file.exists():
                try:
                    with open(self._cache_file, "r", encoding="utf-8") as f:
                        return json.load(f).get("content", "")
                except Exception:
                    pass
            return "GitHub profile data not available."

    async def _fetch_profile_content(self) -> str:
        """Fetch user profile and top repos from the GitHub REST API asynchronously."""
        username = config.github_username
        
        async with httpx.AsyncClient(headers=self._headers, timeout=config.request_timeout) as client:
            # Fetch profile and repos in parallel
            profile_task = self._get_user_profile(client, username)
            repos_task = self._get_top_repos(client, username)
            
            profile, repos = await asyncio.gather(profile_task, repos_task)

            sections: List[str] = []

            if profile:
                bio = profile.get("bio") or ""
                company = profile.get("company") or ""
                location = profile.get("location") or ""
                blog = profile.get("blog") or ""
                public_repos = profile.get("public_repos", 0)
                followers = profile.get("followers", 0)

                profile_lines = [f"GitHub username: {username}"]
                if bio:
                    profile_lines.append(f"Bio: {bio}")
                if company:
                    profile_lines.append(f"Company: {company}")
                if location:
                    profile_lines.append(f"Location: {location}")
                if blog:
                    profile_lines.append(f"Website: {blog}")
                profile_lines.append(
                    f"Public repos: {public_repos} | Followers: {followers}"
                )
                sections.append("\n".join(profile_lines))

            if repos:
                # Fetch README snippets for top repos in parallel
                readme_tasks = [self._get_readme_snippet(client, username, repo.get("name", "")) for repo in repos]
                readmes = await asyncio.gather(*readme_tasks)
                
                repo_sections: List[str] = []
                for repo, readme in zip(repos, readmes):
                    repo_text = self._format_repo(repo, readme)
                    if repo_text:
                        repo_sections.append(repo_text)
                
                if repo_sections:
                    sections.append("### Top Repositories\n\n" + "\n\n".join(repo_sections))

        return "\n\n".join(sections) if sections else "No GitHub data found."

    async def _get_user_profile(self, client: httpx.AsyncClient, username: str) -> Optional[Dict[str, Any]]:
        """Fetch public user profile from GitHub API asynchronously."""
        try:
            response = await client.get(f"{self._REST_URL}/users/{username}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching GitHub profile: {e}")
            return None

    async def _get_top_repos(self, client: httpx.AsyncClient, username: str, count: int = 6) -> List[Dict[str, Any]]:
        """Fetch top public repos sorted by stars asynchronously."""
        try:
            response = await client.get(
                f"{self._REST_URL}/users/{username}/repos",
                params={"sort": "pushed", "per_page": 30, "type": "owner"},
            )
            response.raise_for_status()
            repos: List[Dict[str, Any]] = response.json()
            # Filter out forks, sort by stars descending, take top N
            owned = [r for r in repos if not r.get("fork", False)]
            owned.sort(key=lambda r: r.get("stargazers_count", 0), reverse=True)
            return owned[:count]
        except httpx.HTTPError as e:
            logger.error(f"Error fetching GitHub repos: {e}")
            return []

    def _format_repo(self, repo: Dict[str, Any], readme_snippet: str = "") -> str:
        """Format a repo dict and readme snippet into a readable text block."""
        name = repo.get("name", "")
        description = repo.get("description") or ""
        language = repo.get("language") or ""
        stars = repo.get("stargazers_count", 0)
        topics: List[str] = repo.get("topics") or []
        url = repo.get("html_url", "")

        lines = [f"**{name}** ({url})"]
        if description:
            lines.append(f"  {description}")
        meta_parts = []
        if language:
            meta_parts.append(f"Language: {language}")
        if stars:
            meta_parts.append(f"Stars: {stars}")
        if topics:
            meta_parts.append(f"Topics: {', '.join(topics[:5])}")
        if meta_parts:
            lines.append("  " + " | ".join(meta_parts))

        if readme_snippet:
            lines.append(f"  README: {readme_snippet}")

        return "\n".join(lines)

    async def _get_readme_snippet(self, client: httpx.AsyncClient, username: str, repo_name: str, max_chars: int = 300) -> str:
        """Fetch and return the first max_chars of a repo's README asynchronously."""
        if not repo_name:
            return ""
            
        try:
            response = await client.get(f"{self._REST_URL}/repos/{username}/{repo_name}/readme")
            if response.status_code == 404:
                return ""
            response.raise_for_status()
            data = response.json()
            raw = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
            # Strip markdown headings and blank lines for a clean snippet
            lines = [
                l.strip()
                for l in raw.splitlines()
                if l.strip() and not l.strip().startswith("#")
            ]
            snippet = " ".join(lines)[:max_chars]
            return snippet + "…" if len(snippet) == max_chars else snippet
        except Exception as e:
            logger.debug(f"Could not fetch README for {repo_name}: {e}")
            return ""

    def _get_cached_content(self) -> Optional[str]:
        """Return cached content if still within TTL, else None."""
        try:
            if not self._cache_file.exists():
                return None
            with open(self._cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            age = time.time() - cache_data.get("timestamp", 0)
            if age < config.github_cache_duration:
                return cache_data.get("content")
            return None
        except Exception as e:
            logger.error(f"Error reading GitHub cache: {e}")
            return None

    def _cache_content(self, content: str) -> None:
        """Persist content to the cache file."""
        try:
            config.static_dir.mkdir(parents=True, exist_ok=True)
            cache_data = {
                "content": content,
                "timestamp": time.time(),
                "username": config.github_username,
            }
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info("GitHub content cached successfully")
        except Exception as e:
            logger.error(f"Error caching GitHub content: {e}")
