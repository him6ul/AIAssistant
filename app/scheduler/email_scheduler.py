"""
Email ingestion scheduler - runs periodically to ingest emails.
"""

import asyncio
from typing import Optional
from app.ingestion.email_o365_ingestor import EmailO365Ingestor
from app.ingestion.email_imap_ingestor import EmailIMAPIngestor
from app.tasks.extractor import get_task_extractor
from app.tasks.models import TaskExtractionRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailScheduler:
    """
    Schedules and runs email ingestion tasks.
    """
    
    def __init__(
        self,
        interval_seconds: int = 900,  # 15 minutes
        use_o365: bool = True,
        use_imap: bool = False,
        o365_config: Optional[dict] = None,
        imap_config: Optional[dict] = None
    ):
        """
        Initialize email scheduler.
        
        Args:
            interval_seconds: Interval between ingestion runs
            use_o365: Use Office 365 ingestion
            use_imap: Use IMAP ingestion
            o365_config: Office 365 configuration
            imap_config: IMAP configuration
        """
        self.interval_seconds = interval_seconds
        self.use_o365 = use_o365
        self.use_imap = use_imap
        self._running = False
        
        # Initialize ingestor
        self.o365_ingestor: Optional[EmailO365Ingestor] = None
        if use_o365:
            try:
                self.o365_ingestor = EmailO365Ingestor(
                    action_keywords=o365_config.get("action_keywords", []) if o365_config else []
                )
            except (ValueError, Exception) as e:
                logger.warning(f"Failed to initialize O365 ingestor: {e}. O365 email features will be disabled.")
                self.o365_ingestor = None
        
        self.imap_ingestor: Optional[EmailIMAPIngestor] = None
        if use_imap and imap_config:
            self.imap_ingestor = EmailIMAPIngestor(
                server=imap_config.get("server", ""),
                port=imap_config.get("port", 993),
                username=imap_config.get("username", ""),
                password=imap_config.get("password", ""),
                use_ssl=imap_config.get("use_ssl", True),
                action_keywords=imap_config.get("action_keywords", [])
            )
        
        self.task_extractor = get_task_extractor()
    
    async def _ingest_and_extract(self):
        """
        Ingest emails and extract tasks.
        """
        logger.info("Starting scheduled email ingestion")
        
        all_emails = []
        
        # Ingest from Office 365
        if self.o365_ingestor:
            try:
                emails = await self.o365_ingestor.ingest_unread(max_emails=50)
                all_emails.extend(emails)
                
                emails = await self.o365_ingestor.ingest_flagged(max_emails=50)
                all_emails.extend(emails)
            except Exception as e:
                logger.error(f"Office 365 ingestion failed: {e}")
        
        # Ingest from IMAP
        if self.imap_ingestor:
            try:
                emails = await self.imap_ingestor.ingest_unread(max_emails=50)
                all_emails.extend(emails)
            except Exception as e:
                logger.error(f"IMAP ingestion failed: {e}")
        
        # Extract tasks from emails
        for email_data in all_emails:
            try:
                content = f"Subject: {email_data.get('subject', '')}\n\n{email_data.get('body', '')}"
                
                request = TaskExtractionRequest(
                    content=content,
                    source="email",
                    source_id=email_data.get("id")
                )
                
                await self.task_extractor.extract_and_store(request)
            except Exception as e:
                logger.error(f"Task extraction failed for email {email_data.get('id')}: {e}")
        
        logger.info(f"Email ingestion completed: {len(all_emails)} emails processed")
    
    async def start(self):
        """
        Start the scheduler.
        """
        if self._running:
            logger.warning("Email scheduler already running")
            return
        
        self._running = True
        logger.info(f"Starting email scheduler (interval: {self.interval_seconds}s)")
        
        # Run immediately once
        await self._ingest_and_extract()
        
        # Then run periodically
        while self._running:
            await asyncio.sleep(self.interval_seconds)
            if self._running:
                await self._ingest_and_extract()
    
    def stop(self):
        """
        Stop the scheduler.
        """
        self._running = False
        logger.info("Email scheduler stopped")

