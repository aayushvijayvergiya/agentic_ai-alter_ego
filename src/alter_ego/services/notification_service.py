"""Notification services for the Alter Ego application."""

import requests
from typing import Optional

from ..config import config


class NotificationService:
    """Service for sending notifications via various channels."""
    
    def __init__(self):
        self.pushover_enabled = config.has_pushover_config
        
        if self.pushover_enabled:
            print(f"Pushover user found and starts with {config.pushover_user[0]}")
            print(f"Pushover token found and starts with {config.pushover_token[0]}")
        else:
            print("Pushover configuration not found - notifications disabled")
    
    def send_notification(self, message: str) -> bool:
        """Send a notification message."""
        print(f"Notification: {message}")
        
        if not self.pushover_enabled:
            print("Pushover not configured - skipping notification")
            return False
        
        try:
            payload = {
                "user": config.pushover_user,
                "token": config.pushover_token,
                "message": message
            }
            
            response = requests.post(config.pushover_url, data=payload)
            response.raise_for_status()
            
            return True
            
        except requests.RequestException as e:
            print(f"Failed to send notification: {e}")
            return False
    
    def notify_user_interest(self, email: str, name: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Send notification when a user shows interest."""
        name_part = name or "Name not provided"
        notes_part = notes or "not provided"
        message = f"Recording interest from {name_part} with email {email} and notes {notes_part}"
        return self.send_notification(message)
    
    def notify_unknown_question(self, question: str) -> bool:
        """Send notification when an unknown question is recorded."""
        message = f"Recording question: '{question}'"
        return self.send_notification(message)
