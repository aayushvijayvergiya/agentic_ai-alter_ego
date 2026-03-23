"""Notification services for the Alter Ego application."""

import asyncio
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

import httpx

from ..config import config
from ..utils.logger import logger


class NotificationService:
    """Service for sending notifications via SMTP or Pushover."""
    
    def __init__(self):
        self.smtp_enabled = config.has_smtp_config
        self.pushover_enabled = config.has_pushover_config
        
        if self.smtp_enabled:
            logger.info(f"SMTP notifications enabled (Host: {config.smtp_host}, Port: {config.smtp_port})")
        
        if self.pushover_enabled:
            logger.info("Pushover notifications enabled")
            
        if not self.smtp_enabled and not self.pushover_enabled:
            logger.warning("No notification channels configured (SMTP or Pushover)")
    
    async def send_notification(self, message: str, subject: str = "Alter Ego Notification") -> bool:
        """Send a notification message via available channels."""
        logger.info(f"Sending notification: {message}")
        
        success = False
        
        # Try SMTP first if enabled
        if self.smtp_enabled:
            smtp_success = await asyncio.to_thread(self._send_email_sync, subject, message)
            if smtp_success:
                success = True
        
        # Try Pushover as secondary or fallback
        if self.pushover_enabled:
            pushover_success = await self._send_pushover_async(message)
            if pushover_success:
                success = True
                
        if not self.smtp_enabled and not self.pushover_enabled:
            logger.debug("No notification channels configured - skipping")
            
        return success

    def _send_email_sync(self, subject: str, body: str) -> bool:
        """Send an email using smtplib (synchronous)."""
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = config.smtp_user
            msg['To'] = config.notification_email

            context = ssl.create_default_context()
            
            with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
                server.starttls(context=context)
                server.login(config.smtp_user, config.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {config.notification_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False

    async def _send_pushover_async(self, message: str) -> bool:
        """Send a Pushover notification asynchronously."""
        try:
            payload = {
                "user": config.pushover_user,
                "token": config.pushover_token,
                "message": message
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(config.pushover_url, data=payload)
                response.raise_for_status()
            
            logger.info("Pushover notification sent successfully")
            return True
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to send notification via Pushover: {e}")
            return False
    
    async def notify_user_interest(self, email: str, name: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """Send notification when a user shows interest asynchronously."""
        name_part = name or "Name not provided"
        notes_part = notes or "not provided"
        message = f"Recording interest from {name_part} with email {email} and notes {notes_part}"
        subject = f"Alter Ego: Interest from {name_part}"
        return await self.send_notification(message, subject=subject)
    
    async def notify_unknown_question(self, question: str) -> bool:
        """Send notification when an unknown question is recorded asynchronously."""
        message = f"Recording unknown question: '{question}'"
        subject = "Alter Ego: Unknown Question Recorded"
        return await self.send_notification(message, subject=subject)
