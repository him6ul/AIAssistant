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
        logger.debug(f"      🔍 Checking importance for: '{email.subject}'")
        
        # Heuristic checks first (fast)
        if email.is_important:
            logger.debug(f"      ✅ IMPORTANT (heuristic): is_important flag is True")
            return True
        
        if email.priority and email.priority.value in ["high", "urgent"]:
            logger.debug(f"      ✅ IMPORTANT (heuristic): priority is {email.priority.value}")
            return True
        
        # Check for important keywords in subject
        important_keywords = [
            "urgent", "important", "action required", "deadline", "meeting",
            "asap", "critical", "priority", "attention", "response needed"
        ]
        subject_lower = email.subject.lower()
        matching_keywords = [kw for kw in important_keywords if kw in subject_lower]
        if matching_keywords:
            logger.debug(f"      ✅ IMPORTANT (heuristic): found keywords in subject: {matching_keywords}")
            return True
        
        # Use LLM for more nuanced detection
        logger.debug(f"      🤖 Using LLM for importance analysis...")
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

            llm_start = datetime.utcnow()
            response = await self.llm_router.generate(
                prompt=prompt,
                system_prompt="You are an email importance analyzer. Respond with only YES or NO."
            )
            llm_duration = (datetime.utcnow() - llm_start).total_seconds()
            
            if response and "content" in response:
                result = response["content"].strip().upper()
                is_important_result = result.startswith("YES")
                logger.debug(f"      {'✅' if is_important_result else '❌'} IMPORTANT (LLM): {result} (took {llm_duration:.2f}s)")
                return is_important_result
            else:
                logger.debug(f"      ❌ IMPORTANT (LLM): No valid response from LLM")
            return False
        except Exception as e:
            logger.error(f"      ❌ Error checking email importance with LLM: {e}")
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
        check_start_time = datetime.utcnow()
        since = check_start_time - timedelta(minutes=self.lookback_minutes)
        
        # Get enabled mail connectors from registry
        enabled_mail_connectors = self.orchestrator.registry.get_all_mail_connectors()
        enabled_source_types = list(enabled_mail_connectors.keys())
        source_names = [st.value.title() for st in enabled_source_types]
        
        logger.info("=" * 80)
        logger.info(f"📧 EMAIL MONITOR CHECK STARTED at {check_start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info(f"   Checking for emails since: {since.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        logger.info(f"   Lookback window: {self.lookback_minutes} minutes")
        logger.info(f"   Sources to check: {', '.join(source_names) if source_names else 'None (no mail connectors enabled)'}")
        logger.info("-" * 80)
        
        if not enabled_source_types:
            logger.warning("⚠️  No mail connectors enabled - skipping email check")
            return []
        
        try:
            # Fetch emails from all enabled mail connectors
            # Check both unread and read emails to catch important ones
            logger.info(f"🔍 Fetching emails from {len(enabled_source_types)} configured source(s)...")
            fetch_start = datetime.utcnow()
            
            emails = await self.orchestrator.get_all_emails(
                source_types=enabled_source_types,
                unread_only=False,  # Check all emails, not just unread
                limit=10  # Reduced from 50 to avoid large pickling issues with ProcessPoolExecutor
            )
            
            fetch_duration = (datetime.utcnow() - fetch_start).total_seconds()
            
            # Count emails by source
            emails_by_source = {}
            for email in emails:
                source = email.source_type.value
                emails_by_source[source] = emails_by_source.get(source, 0) + 1
            
            logger.info(f"✅ Fetched {len(emails)} total emails in {fetch_duration:.2f}s")
            for source, count in emails_by_source.items():
                logger.info(f"   - {source}: {count} emails")
            
            # Log details of ALL fetched emails (before filtering)
            if emails:
                logger.info("📋 All fetched emails details:")
                for idx, email in enumerate(emails[:10], 1):  # Show first 10
                    sender = email.from_address.get('email', 'Unknown')
                    sender_name = email.from_address.get('name', '')
                    if sender_name:
                        sender_display = f"{sender_name} <{sender}>"
                    else:
                        sender_display = sender
                    logger.info(f"   {idx}. [{email.source_type.value}] '{email.subject}' from {sender_display} at {email.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    logger.info(f"      ID: {email.id}, Important flag: {email.is_important}, Priority: {email.priority}")
                if len(emails) > 10:
                    logger.info(f"   ... and {len(emails) - 10} more emails")
            
            # Filter emails from the last N minutes
            logger.info(f"⏰ Filtering emails from last {self.lookback_minutes} minutes...")
            recent_emails = [
                email for email in emails
                if email.timestamp >= since
            ]
            
            recent_by_source = {}
            for email in recent_emails:
                source = email.source_type.value
                recent_by_source[source] = recent_by_source.get(source, 0) + 1
            
            logger.info(f"✅ Found {len(recent_emails)} emails from last {self.lookback_minutes} minutes")
            for source, count in recent_by_source.items():
                logger.info(f"   - {source}: {count} recent emails")
            
            # Log details of recent emails
            if recent_emails:
                logger.info("📋 Recent emails details:")
                for idx, email in enumerate(recent_emails, 1):
                    sender = email.from_address.get('email', 'Unknown')
                    sender_name = email.from_address.get('name', '')
                    if sender_name:
                        sender_display = f"{sender_name} <{sender}>"
                    else:
                        sender_display = sender
                    logger.info(f"   {idx}. [{email.source_type.value}] '{email.subject}' from {sender_display} at {email.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                    logger.info(f"      ID: {email.id}, Important flag: {email.is_important}, Priority: {email.priority}")
            else:
                logger.info("   No recent emails found in the time window")
            
            # Filter out already notified emails
            logger.info(f"🔍 Checking for previously notified emails (tracking {len(self._notified_email_ids)} notified IDs)...")
            new_emails = [
                email for email in recent_emails
                if email.id not in self._notified_email_ids
            ]
            
            logger.info(f"✅ Found {len(new_emails)} new emails (not previously notified)")
            if len(new_emails) < len(recent_emails):
                logger.info(f"   ({len(recent_emails) - len(new_emails)} emails were already notified)")
            
            # Check importance
            logger.info("🎯 Checking email importance...")
            important_emails = []
            importance_checks = {"heuristic": 0, "llm": 0, "total_checked": 0}
            
            for idx, email in enumerate(new_emails, 1):
                logger.info(f"   [{idx}/{len(new_emails)}] Checking: '{email.subject}' from {email.from_address.get('email', 'Unknown')}")
                
                # Log email details
                logger.info(f"      - Source: {email.source_type.value}")
                logger.info(f"      - Timestamp: {email.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                logger.info(f"      - Is Important Flag: {email.is_important}")
                logger.info(f"      - Priority: {email.priority}")
                
                is_important = await self.importance_checker.is_important(email)
                importance_checks["total_checked"] += 1
                
                if is_important:
                    important_emails.append(email)
                    logger.info(f"      ✅ RESULT: IMPORTANT - Will notify user")
                else:
                    logger.info(f"      ❌ RESULT: Not important - Skipping")
            
            logger.info("-" * 80)
            logger.info(f"📊 IMPORTANCE CHECK SUMMARY:")
            logger.info(f"   Total emails checked: {importance_checks['total_checked']}")
            logger.info(f"   Important emails found: {len(important_emails)}")
            logger.info(f"   Not important: {importance_checks['total_checked'] - len(important_emails)}")
            
            check_duration = (datetime.utcnow() - check_start_time).total_seconds()
            logger.info(f"⏱️  Total check duration: {check_duration:.2f}s")
            logger.info("=" * 80)
            
            return important_emails
        except Exception as e:
            check_duration = (datetime.utcnow() - check_start_time).total_seconds()
            logger.error("=" * 80)
            logger.error(f"❌ ERROR in email check (duration: {check_duration:.2f}s): {e}", exc_info=True)
            logger.error("=" * 80)
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
            
            logger.info(f"🔊 Speaking notification for email: '{subject}' from {sender_name}")
            logger.info(f"   Notification text: {notification}")
            
            # Speak the notification
            await asyncio.to_thread(self.tts_engine.speak, notification)
            
            # Mark as notified
            self._notified_email_ids.add(email.id)
            self._save_notification_history()
            
            logger.info(f"✅ Notification completed and email marked as notified (ID: {email.id})")
            
        except Exception as e:
            logger.error(f"❌ Error notifying about email: {e}", exc_info=True)
    
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
                logger.info("ℹ️  No new important emails found - no notification needed")
                return
            
            logger.info("🔔 NOTIFICATION PHASE")
            logger.info(f"   Found {len(important_emails)} new important email(s) to notify about")
            
            if len(important_emails) == 1:
                email = important_emails[0]
                logger.info(f"   Notifying about single email: '{email.subject}' from {email.from_address.get('email', 'Unknown')}")
                await self._notify_about_email(email)
            else:
                logger.info(f"   Notifying about {len(important_emails)} emails")
                await self._notify_about_multiple_emails(important_emails)
            
            logger.info("✅ Notification phase completed")
                
        except Exception as e:
            logger.error(f"❌ Error in check and notify: {e}", exc_info=True)
    
    async def start(self):
        """Start the email monitoring service."""
        if self._running:
            logger.warning("⚠️  Email notification monitor already running")
            return
        
        logger.info("=" * 80)
        logger.info("🚀 STARTING EMAIL NOTIFICATION MONITOR")
        logger.info(f"   Check interval: {self.check_interval_seconds}s ({self.check_interval_seconds/60:.1f} minutes)")
        logger.info(f"   Lookback window: {self.lookback_minutes} minutes")
        logger.info(f"   Tracking {len(self._notified_email_ids)} previously notified emails")
        logger.info("=" * 80)
        
        # Initialize orchestrator (connectors should already be loaded by main.py)
        # The orchestrator will use the global registry which has connectors registered
        logger.info("🔌 Initializing connectors...")
        
        # Add timeout to prevent hanging
        import asyncio
        try:
            initialized = await asyncio.wait_for(self.orchestrator.initialize(), timeout=60.0)
            if not initialized:
                logger.warning("⚠️  Email monitor orchestrator initialization returned False - connectors may not be available")
                # Continue anyway - connectors might already be connected from main.py
            else:
                logger.info("✅ Connectors initialized successfully")
        except asyncio.TimeoutError:
            logger.error("❌ Timeout initializing orchestrator (60s) - continuing anyway")
            # Continue - connectors might already be connected
        except Exception as e:
            logger.error(f"❌ Error initializing orchestrator: {e}", exc_info=True)
            # Continue - connectors might already be connected
        
        self._running = True
        
        # Run immediately once
        logger.info("▶️  Running initial email check...")
        try:
            await self._check_and_notify()
        except Exception as e:
            logger.error(f"❌ Error in initial email check: {e}", exc_info=True)
        
        # Then run periodically - use same pattern as working schedulers
        check_count = 1
        logger.info(f"🔄 Starting periodic check loop (interval: {self.check_interval_seconds}s)")
        logger.info(f"   Task info: Running in event loop: {asyncio.get_running_loop() is not None}")
        while self._running:
            logger.info(f"⏳ Next check in {self.check_interval_seconds}s (check #{check_count} completed)")
            logger.info(f"   Monitor running: {self._running}, check_count: {check_count}")
            try:
                # Use simple asyncio.sleep like the working schedulers do
                logger.info(f"   Sleeping for {self.check_interval_seconds} seconds...")
                await asyncio.sleep(self.check_interval_seconds)
                logger.info(f"   ✅ Sleep completed at {datetime.utcnow().strftime('%H:%M:%S')} UTC, checking if still running...")
                if self._running:
                    check_count += 1
                    logger.info(f"🔄 Starting periodic check #{check_count}...")
                    try:
                        await self._check_and_notify()
                        logger.info(f"   ✅ Periodic check #{check_count} completed")
                    except Exception as e:
                        logger.error(f"❌ Error in periodic check #{check_count}: {e}", exc_info=True)
                        # Continue the loop even if check fails
                else:
                    logger.info("   Monitor stopped, exiting loop")
                    break
            except asyncio.CancelledError:
                logger.warning("   ⚠️  Monitor task cancelled - this should not happen during normal operation")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitor loop: {e}", exc_info=True)
                # Wait a bit before retrying to avoid tight error loop
                await asyncio.sleep(10)
    
    def stop(self):
        """Stop the email monitoring service."""
        self._running = False
        logger.info("Email notification monitor stopped")
    
    async def shutdown(self):
        """Shutdown the monitor and cleanup."""
        self.stop()
        await self.orchestrator.shutdown()

