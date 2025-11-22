"""
Outlook connector using Microsoft Graph API.
"""

from typing import List, Optional
from datetime import datetime
from app.connectors.base import BaseConnector, ConnectorType, Message
from app.ingestion.ms_graph_client import MSGraphClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OutlookConnector(BaseConnector):
    """Outlook connector using Microsoft Graph API."""
    
    def __init__(self, name: str = "outlook", **kwargs):
        """Initialize Outlook connector."""
        super().__init__(name, ConnectorType.EMAIL)
        self.graph_client: Optional[MSGraphClient] = None
    
    async def initialize(self) -> bool:
        """Initialize Outlook connector."""
        try:
            self.graph_client = MSGraphClient()
            await self.graph_client.authenticate()
            self.initialized = True
            logger.info("Outlook connector initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Outlook connector: {e}")
            self.initialized = False
            return False
    
    async def is_available(self) -> bool:
        """Check if Outlook connector is available."""
        if not self.graph_client:
            return False
        try:
            return await self.graph_client.is_authenticated()
        except Exception:
            return False
    
    async def get_messages(
        self,
        limit: int = 50,
        unread_only: bool = False,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """Get messages from Outlook."""
        if not self.graph_client:
            return []
        
        try:
            # Use existing email ingestor logic
            from app.ingestion.email_o365_ingestor import EmailO365Ingestor
            ingestor = EmailO365Ingestor()
            emails = await ingestor.ingest_unread(max_emails=limit)
            
            messages = []
            for email_data in emails:
                message = Message(
                    id=email_data.get("id", ""),
                    subject=email_data.get("subject", ""),
                    body=email_data.get("body", ""),
                    sender=email_data.get("from", ""),
                    timestamp=datetime.fromisoformat(email_data.get("receivedDateTime", datetime.now().isoformat())),
                    metadata=email_data
                )
                messages.append(message)
            
            return messages
        except Exception as e:
            logger.error(f"Error getting Outlook messages: {e}")
            return []
    
    async def send_message(
        self,
        to: str,
        subject: Optional[str],
        body: str,
        **kwargs
    ) -> bool:
        """Send message via Outlook."""
        if not self.graph_client:
            return False
        
        try:
            # Implement send message via Graph API
            # This would use the Graph API to send an email
            logger.info(f"Sending Outlook message to {to}")
            # TODO: Implement actual send via Graph API
            return True
        except Exception as e:
            logger.error(f"Error sending Outlook message: {e}")
            return False

