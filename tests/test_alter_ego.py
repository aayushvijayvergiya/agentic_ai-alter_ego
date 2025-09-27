"""Tests for the Alter Ego application."""

import pytest
from unittest.mock import Mock, patch

from src.alter_ego.config import Config
from src.alter_ego.models import UserDetails, UnknownQuestion
from src.alter_ego.services.notification_service import NotificationService


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


if __name__ == "__main__":
    pytest.main([__file__])
