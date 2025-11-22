"""
Gmail connector using IMAP.
"""

from typing import List, Optional
from datetime import datetime
import imaplib
import email
from email.header import decode_header
from app.connectors.base import BaseConnector, ConnectorType, Message
from app.utils.logger import get_logger
import os

logger = get_logger(__name__)


class GmailConnector(BaseConnector):
    """Gmail connector using IMAP."""
    
    def __init__(self, name: str = "gmail", **kwargs):
        """Initialize Gmail connector."""
        super().__init__(name, ConnectorType.EMAIL)
        self.imap_server = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
        self.imap_port = int(os.getenv("EMAIL_IMAP_PORT", "993"))
        self.username = os.getenv("EMAIL_IMAP_USERNAME")
        self.password = os.getenv("EMAIL_IMAP_PASSWORD")
        self.imap: Optional[imaplib.IMAP4_SSL] = None
    
    async def initialize(self) -> bool:
        """Initialize Gmail connector."""
        if not self.username or not self.password:
            logger.warning("Gmail credentials not configured")
            return False
        
        try:
            # IMAP operations are blocking, so we run them in executor
            import asyncio
            loop = asyncio.get_event_loop()
            self.imap = await loop.run_in_executor(
                None,
                lambda: imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            )
            await loop.run_in_executor(
                None,
                lambda: self.imap.login(self.username, self.password)
            )
            self.initialized = True
            logger.info("Gmail connector initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Gmail connector: {e}")
            self.initialized = False
            return False
    
    async def is_available(self) -> bool:
        """Check if Gmail connector is available."""
        return self.initialized and self.imap is not None
    
    async def get_messages(
        self,
        limit: int = 50,
        unread_only: bool = False,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """Get messages from Gmail."""
        if not self.imap:
            return []
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Run blocking IMAP operations in executor
            await loop.run_in_executor(None, lambda: self.imap.select("INBOX"))
            
            search_criteria = "UNSEEN" if unread_only else "ALL"
            if since:
                search_criteria += f' SINCE {since.strftime("%d-%b-%Y")}'
            
            status, messages = await loop.run_in_executor(
                None,
                lambda: self.imap.search(None, search_criteria)
            )
            if status != "OK":
                return []
            
            message_ids = messages[0].split()[:limit]
            result_messages = []
            
            for msg_id in message_ids:
                status, msg_data = await loop.run_in_executor(
                    None,
                    lambda mid=msg_id: self.imap.fetch(mid, "(RFC822)")
                )
                if status != "OK":
                    continue
                
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                subject = decode_header(email_message["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                sender = email_message["From"]
                date_tuple = email.utils.parsedate_tz(email_message["Date"])
                if date_tuple:
                    timestamp = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                else:
                    timestamp = datetime.now()
                
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = email_message.get_payload(decode=True).decode()
                
                message = Message(
                    id=msg_id.decode(),
                    subject=subject or "",
                    body=body,
                    sender=sender or "",
                    timestamp=timestamp,
                    metadata={"raw": email_message}
                )
                result_messages.append(message)
            
            return result_messages
        except Exception as e:
            logger.error(f"Error getting Gmail messages: {e}")
            return []
    
    async def send_message(
        self,
        to: str,
        subject: Optional[str],
        body: str,
        **kwargs
    ) -> bool:
        """Send message via Gmail (would need SMTP)."""
        logger.warning("Gmail send not implemented via IMAP - use SMTP")
        return False

