"""
Email monitoring service that checks for new important emails and notifies the user.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Set, List, Optional
from pathlib import Path
import json

from app.connectors.orchestrator import AssistantOrchestrator
from app.connectors.models import UnifiedEmail, SourceType
from app.llm_router import get_llm_router
from app.tts import TTSEngine
from app.utils.localization import get_message
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailImportanceChecker:
    """Checks if an email is important using LLM."""
    
    def __init__(self):
        self.llm_router = get_llm_router()
    
    async def is_important(self, email: UnifiedEmail) -> bool:
        """
        Determine if an email is important.
        
        Args:
            email: UnifiedEmail object
        
        Returns:
            True if email is important, False otherwise
        """
        # Heuristic checks first (fast)
        if email.is_important:
            return True
        
        if email.priority and email.priority.value in ["high", "urgent"]:
            return True
        
        # Check for important keywords in subject
        important_keywords = [
            "urgent", "important", "action required", "deadline", "meeting",
            "asap", "critical", "priority", "attention", "response needed"
        ]
        subject_lower = email.subject.lower()
        if any(keyword in subject_lower for keyword in important_keywords):
            return True
        
        # Use LLM for more nuanced detection
        try:
            prompt = f"""Analyze this email and determine if it's important and requires immediate attention.

Subject: {email.subject}
From: {email.from_address.get('name', '')} <{email.from_address.get('email', '')}>
Body preview: {email.body_text[:500] if email.body_text else 'No body text'}

Consider:
- Is it urgent or time-sensitive?
- Does it require action or response?
- Is it from an important contact or organization?
- Does it contain deadlines or critical information?

Respond with only "YES" if important, or "NO" if not important."""

            response = await self.llm_router.generate(
                prompt=prompt,
                system_prompt="You are an email importance analyzer. Respond with only YES or NO."
            )
            
            if response and "content" in response:
                result = response["content"].strip().upper()
                return result.startswith("YES")
            return False
        except Exception as e:
            logger.error(f"Error checking email importance with LLM: {e}")
            # Default to not important if LLM check fails
            return False


class EmailNotificationMonitor:
    """
    Monitors emails from Gmail and Outlook for new important emails.
    Notifies the user via TTS when important emails are detected.
    """
    
    def __init__(
        self,
        check_interval_seconds: int = 300,  # 5 minutes
        lookback_minutes: int = 5
    ):
        """
        Initialize email notification monitor.
        
        Args:
            check_interval_seconds: How often to check for new emails (default: 300 = 5 minutes)
            lookback_minutes: How many minutes back to check for new emails (default: 5)
        """
        self.check_interval_seconds = check_interval_seconds
        self.lookback_minutes = lookback_minutes
        self._running = False
        self._notified_email_ids: Set[str] = set()
        
        # Initialize orchestrator (will use global registry with loaded connectors)
        self.orchestrator = AssistantOrchestrator()
        self.importance_checker = EmailImportanceChecker()
        
        # Initialize TTS
        self.tts_engine = TTSEngine()
        
        # Load notified emails from disk (persist across restarts)
        self._notification_history_file = Path("data/email_notifications.json")
        self._load_notification_history()
    
    def _load_notification_history(self):
        """Load previously notified email IDs from disk."""
        if self._notification_history_file.exists():
            try:
                with open(self._notification_history_file, "r") as f:
                    data = json.load(f)
                    self._notified_email_ids = set(data.get("notified_ids", []))
                logger.info(f"Loaded {len(self._notified_email_ids)} previously notified email IDs")
            except Exception as e:
                logger.error(f"Error loading notification history: {e}")
    
    def _save_notification_history(self):
        """Save notified email IDs to disk."""
        try:
            self._notification_history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._notification_history_file, "w") as f:
                json.dump({"notified_ids": list(self._notified_email_ids)}, f)
        except Exception as e:
            logger.error(f"Error saving notification history: {e}")
    
    async def _check_for_important_emails(self) -> List[UnifiedEmail]:
        """
        Check for new important emails in the last N minutes.
        
        Returns:
            List of new important emails
        """
        try:
            # Calculate time threshold
            since = datetime.utcnow() - timedelta(minutes=self.lookback_minutes)
            logger.info(f"Checking for emails since {since.isoformat()} (last {self.lookback_minutes} minutes)")
            
            # Fetch emails from Gmail and Outlook
            emails = await self.orchestrator.get_all_emails(
                source_types=[SourceType.GMAIL, SourceType.OUTLOOK],
                unread_only=True,
                limit=50
            )
            
            logger.info(f"Fetched {len(emails)} total emails from all sources")
            
            # Filter emails from the last N minutes
            recent_emails = [
                email for email in emails
                if email.timestamp >= since
            ]
            
            logger.info(f"Found {len(recent_emails)} emails from last {self.lookback_minutes} minutes")
            for email in recent_emails:
                logger.debug(f"Recent email: {email.subject} from {email.from_address.get('email', 'Unknown')} at {email.timestamp.isoformat()}")
            
            # Filter out already notified emails
            new_emails = [
                email for email in recent_emails
                if email.id not in self._notified_email_ids
            ]
            
            logger.info(f"Found {len(new_emails)} new emails (not previously notified)")
            
            # Check importance
            important_emails = []
            for email in new_emails:
                is_important = await self.importance_checker.is_important(email)
                logger.info(f"Email '{email.subject}' importance check: {is_important}")
                if is_important:
                    important_emails.append(email)
            
            logger.info(f"Found {len(important_emails)} important emails")
            return important_emails
        except Exception as e:
            logger.error(f"Error checking for important emails: {e}", exc_info=True)
            return []
    
    async def _notify_about_email(self, email: UnifiedEmail):
        """
        Notify the user about an important email via TTS.
        
        Args:
            email: UnifiedEmail object
        """
        try:
            user_name = os.getenv("USER_NAME", "Himanshu")
            sender_name = email.from_address.get("name") or email.from_address.get("email", "Unknown")
            subject = email.subject or "No subject"
            
            # Get localized message
            prefix = get_message("EMAIL_NOTIFICATION_PREFIX", user_name=user_name)
            subject_line = get_message("EMAIL_NOTIFICATION_SUBJECT", subject=subject)
            from_line = get_message("EMAIL_NOTIFICATION_FROM", sender=sender_name)
            
            # Build notification message
            notification = f"{prefix}. {subject_line}. {from_line}."
            
            logger.info(f"Notifying about important email: {subject} from {sender_name}")
            
            # Speak the notification
            await asyncio.to_thread(self.tts_engine.speak, notification)
            
            # Mark as notified
            self._notified_email_ids.add(email.id)
            self._save_notification_history()
            
        except Exception as e:
            logger.error(f"Error notifying about email: {e}", exc_info=True)
    
    async def _notify_about_multiple_emails(self, emails: List[UnifiedEmail]):
        """
        Notify the user about multiple important emails.
        
        Args:
            emails: List of UnifiedEmail objects
        """
        try:
            user_name = os.getenv("USER_NAME", "Himanshu")
            
            # Get localized message
            prefix = get_message("EMAIL_NOTIFICATION_PREFIX", user_name=user_name)
            multiple_msg = get_message("EMAIL_NOTIFICATION_MULTIPLE", count=len(emails))
            
            notification = f"{prefix}. {multiple_msg}."
            
            logger.info(f"Notifying about {len(emails)} important emails")
            
            # Speak the notification
            await asyncio.to_thread(self.tts_engine.speak, notification)
            
            # Then notify about each email
            for email in emails:
                await self._notify_about_email(email)
                await asyncio.sleep(1)  # Small delay between notifications
            
        except Exception as e:
            logger.error(f"Error notifying about multiple emails: {e}", exc_info=True)
    
    async def _check_and_notify(self):
        """Check for important emails and notify if found."""
        try:
            important_emails = await self._check_for_important_emails()
            
            if not important_emails:
                logger.debug("No new important emails found")
                return
            
            logger.info(f"Found {len(important_emails)} new important email(s)")
            
            if len(important_emails) == 1:
                await self._notify_about_email(important_emails[0])
            else:
                await self._notify_about_multiple_emails(important_emails)
                
        except Exception as e:
            logger.error(f"Error in check and notify: {e}", exc_info=True)
    
    async def start(self):
        """Start the email monitoring service."""
        if self._running:
            logger.warning("Email notification monitor already running")
            return
        
        logger.info(f"Starting email notification monitor (check interval: {self.check_interval_seconds}s, lookback: {self.lookback_minutes} minutes)")
        
        # Initialize orchestrator (connectors should already be loaded by main.py)
        # The orchestrator will use the global registry which has connectors registered
        initialized = await self.orchestrator.initialize()
        if not initialized:
            logger.warning("Email monitor orchestrator initialization returned False - connectors may not be available")
        
        self._running = True
        
        # Run immediately once
        await self._check_and_notify()
        
        # Then run periodically
        while self._running:
            await asyncio.sleep(self.check_interval_seconds)
            if self._running:
                await self._check_and_notify()
    
    def stop(self):
        """Stop the email monitoring service."""
        self._running = False
        logger.info("Email notification monitor stopped")
    
    async def shutdown(self):
        """Shutdown the monitor and cleanup."""
        self.stop()
        await self.orchestrator.shutdown()

