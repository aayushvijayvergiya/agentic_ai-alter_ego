"""Tests for the Alter Ego application."""

import base64
import json
import pytest
from unittest.mock import Mock, MagicMock, patch, mock_open

from src.alter_ego.config import Config
from src.alter_ego.models import UserDetails, UnknownQuestion
from src.alter_ego.services.notification_service import NotificationService
from src.alter_ego.services.github_service import GitHubService


class TestConfig:
    """Test configuration management."""
    
    def test_config_initialization(self):
        """Test that config initializes properly."""
        config = Config()
        assert config.name == "Aayush Vijayvergiya"
        assert config.model_name == "gpt-4o-mini"
    
    def test_pushover_config_detection(self):
        """Test pushover configuration detection."""
        with patch.dict('os.environ', {'PUSHOVER_USER': 'test', 'PUSHOVER_TOKEN': 'test'}):
            config = Config()
            assert config.has_pushover_config is True


class TestModels:
    """Test data models."""
    
    def test_user_details_creation(self):
        """Test UserDetails model creation."""
        user = UserDetails(email="test@example.com", name="Test User")
        assert user.email == "test@example.com"
        assert user.name == "Test User"
    
    def test_unknown_question_creation(self):
        """Test UnknownQuestion model creation."""
        question = UnknownQuestion(question="What is the meaning of life?")
        assert question.question == "What is the meaning of life?"


class TestNotificationService:
    """Test notification service."""
    
    @patch('requests.post')
    def test_send_notification_success(self, mock_post):
        """Test successful notification sending."""
        mock_post.return_value.status_code = 200
        
        with patch.dict('os.environ', {'PUSHOVER_USER': 'test', 'PUSHOVER_TOKEN': 'test'}):
            service = NotificationService()
            result = service.send_notification("Test message")
            assert result is True
    
    def test_send_notification_no_config(self):
        """Test notification when no pushover config."""
        with patch.dict('os.environ', {}, clear=True):
            service = NotificationService()
            result = service.send_notification("Test message")
            assert result is False


class TestGitHubService:
    """Test GitHub integration service."""

    def _make_mock_response(self, json_data: object, status_code: int = 200) -> Mock:
        mock_resp = Mock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data
        mock_resp.raise_for_status = Mock()
        return mock_resp

    @patch("src.alter_ego.services.github_service.GitHubService._get_cached_content", return_value=None)
    @patch("src.alter_ego.services.github_service.GitHubService._cache_content")
    @patch("requests.get")
    def test_fetch_profile_and_repos(self, mock_get: Mock, mock_cache: Mock, mock_cached: Mock) -> None:
        """Test that profile and repo data are fetched and formatted."""
        profile_data = {
            "login": "aayushvijayvergiya",
            "bio": "AI Engineer",
            "company": "Acme Corp",
            "location": "New York",
            "blog": "https://example.com",
            "public_repos": 10,
            "followers": 50,
        }
        readme_content = base64.b64encode(b"This is a test README content.").decode()
        repo_data = [
            {
                "name": "test-repo",
                "description": "A test repository",
                "language": "Python",
                "stargazers_count": 5,
                "topics": ["python", "ai"],
                "html_url": "https://github.com/aayushvijayvergiya/test-repo",
                "fork": False,
            }
        ]

        def side_effect(url: str, **kwargs: object) -> Mock:
            if "/users/" in url and "/repos" not in url:
                return self._make_mock_response(profile_data)
            if "/repos" in url and "/readme" not in url:
                return self._make_mock_response(repo_data)
            if "/readme" in url:
                return self._make_mock_response({"content": readme_content})
            return self._make_mock_response({})

        mock_get.side_effect = side_effect

        service = GitHubService()
        content = service.get_github_content()

        assert "aayushvijayvergiya" in content
        assert "AI Engineer" in content
        assert "test-repo" in content
        assert "Python" in content

    @patch("src.alter_ego.services.github_service.GitHubService._get_cached_content", return_value=None)
    @patch("src.alter_ego.services.github_service.GitHubService._cache_content")
    @patch("requests.get")
    def test_graceful_fallback_on_api_error(self, mock_get: Mock, mock_cache: Mock, mock_cached: Mock) -> None:
        """Test that a failed API call returns a fallback string, not an exception."""
        import requests as req_module
        mock_get.side_effect = req_module.RequestException("Network error")

        service = GitHubService()
        content = service.get_github_content()

        assert isinstance(content, str)
        assert len(content) > 0

    @patch("builtins.open", mock_open(read_data=json.dumps({
        "content": "cached content",
        "timestamp": 9999999999.0,
        "username": "aayushvijayvergiya",
    })))
    @patch("pathlib.Path.exists", return_value=True)
    def test_cache_is_used_when_fresh(self, mock_exists: Mock) -> None:
        """Test that cached content is returned without hitting the API."""
        with patch("requests.get") as mock_get:
            service = GitHubService()
            content = service.get_github_content()
            mock_get.assert_not_called()
            assert content == "cached content"

    @patch("requests.get")
    def test_forks_excluded_from_repos(self, mock_get: Mock) -> None:
        """Test that forked repos are not included in results."""
        repos = [
            {"name": "forked-repo", "fork": True, "stargazers_count": 100,
             "description": "", "language": "Go", "topics": [], "html_url": ""},
            {"name": "own-repo", "fork": False, "stargazers_count": 5,
             "description": "Mine", "language": "Python", "topics": [], "html_url": ""},
        ]
        mock_get.return_value = self._make_mock_response(repos)

        service = GitHubService()
        owned = service._get_top_repos("aayushvijayvergiya")
        assert all(not r.get("fork") for r in owned)
        assert len(owned) == 1
        assert owned[0]["name"] == "own-repo"


if __name__ == "__main__":
    pytest.main([__file__])
