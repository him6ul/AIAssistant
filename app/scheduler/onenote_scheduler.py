"""
OneNote ingestion scheduler - runs periodically to ingest OneNote pages.
"""

import asyncio
from app.ingestion.onenote_ingestor import OneNoteIngestor
from app.tasks.extractor import get_task_extractor
from app.tasks.models import TaskExtractionRequest
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OneNoteScheduler:
    """
    Schedules and runs OneNote ingestion tasks.
    """
    
    def __init__(self, interval_seconds: int = 1800):  # 30 minutes
        """
        Initialize OneNote scheduler.
        
        Args:
            interval_seconds: Interval between ingestion runs
        """
        self.interval_seconds = interval_seconds
        self.ingestor = OneNoteIngestor()
        self.task_extractor = get_task_extractor()
        self._running = False
    
    async def _ingest_and_extract(self):
        """
        Ingest OneNote pages and extract tasks.
        """
        logger.info("Starting scheduled OneNote ingestion")
        
        try:
            pages = await self.ingestor.ingest_new_and_updated(max_pages=100)
            
            # Extract tasks from pages
            for page_data in pages:
                try:
                    content = f"Title: {page_data.get('title', '')}\n\n{page_data.get('content', '')}"
                    
                    request = TaskExtractionRequest(
                        content=content,
                        source="onenote",
                        source_id=page_data.get("id")
                    )
                    
                    await self.task_extractor.extract_and_store(request)
                except Exception as e:
                    logger.error(f"Task extraction failed for page {page_data.get('id')}: {e}")
            
            logger.info(f"OneNote ingestion completed: {len(pages)} pages processed")
        
        except Exception as e:
            logger.error(f"OneNote ingestion failed: {e}")
    
    async def start(self):
        """
        Start the scheduler.
        """
        if self._running:
            logger.warning("OneNote scheduler already running")
            return
        
        self._running = True
        logger.info(f"Starting OneNote scheduler (interval: {self.interval_seconds}s)")
        
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
        logger.info("OneNote scheduler stopped")

