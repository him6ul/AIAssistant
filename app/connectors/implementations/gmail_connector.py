"""
Gmail connector implementation using Google Gmail API.
"""

import os
import imaplib
import email
from email.header import decode_header
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
from app.connectors.base import MailSourceConnector, ConnectorCapabilities
from app.connectors.models import UnifiedEmail, SourceType, EmailPriority
from app.connectors.middleware import with_retry, RetryConfig, with_error_boundary, with_logging
from app.utils.logger import get_logger
import asyncio

logger = get_logger(__name__)


class GmailConnector(MailSourceConnector):
    """
    Gmail connector using IMAP (can be extended to use Gmail API).
    
    This connector implements the MailSourceConnector interface
    and converts Gmail-specific data to UnifiedEmail format.
    """
    
    def __init__(
        self,
        imap_server: Optional[str] = None,
        imap_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize Gmail connector.
        
        Args:
            imap_server: IMAP server address
            imap_port: IMAP server port
            username: Email username
            password: Email password or app password
        """
        self.imap_server = imap_server or os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
        self.imap_port = imap_port or int(os.getenv("EMAIL_IMAP_PORT", "993"))
        self.username = username or os.getenv("EMAIL_IMAP_USERNAME")
        self.password = password or os.getenv("EMAIL_IMAP_PASSWORD")
        self._imap: Optional[imaplib.IMAP4_SSL] = None
        self._connected = False
        self._event_callbacks: List[Callable[[UnifiedEmail], None]] = []
        
        self._retry_config = RetryConfig(max_retries=3, initial_delay=1.0)
    
    @property
    def source_type(self) -> SourceType:
        """Return Gmail source type."""
        return SourceType.GMAIL
    
    @with_logging()
    @with_retry(RetryConfig(max_retries=3))
    async def connect(self) -> bool:
        """Connect to Gmail via IMAP."""
        try:
            if not self.username or not self.password:
                logger.error("Gmail credentials not configured")
                return False
            
            # IMAP operations are blocking, so run in executor
            loop = asyncio.get_event_loop()
            self._imap = await loop.run_in_executor(
                None,
                lambda: imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            )
            await loop.run_in_executor(
                None,
                lambda: self._imap.login(self.username, self.password)
            )
            
            self._connected = True
            logger.info("Gmail connector connected successfully")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Gmail: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Gmail IMAP."""
        if self._imap:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._imap.logout)
            self._imap = None
        self._connected = False
        logger.info("Gmail connector disconnected")
    
    @with_error_boundary("Failed to fetch Gmail emails", return_on_error=[])
    @with_logging()
    async def fetch_emails(
        self,
        limit: int = 50,
        folder: Optional[str] = None,
        unread_only: bool = False,
        since: Optional[datetime] = None,
    ) -> List[UnifiedEmail]:
        """
        Fetch emails from Gmail.
        
        Args:
            limit: Maximum number of emails
            folder: Folder name (inbox, sent, etc.)
            unread_only: Only fetch unread emails
            since: Only fetch emails after this timestamp
        """
        if not self._connected or not self._imap:
            logger.error("Gmail connector not connected")
            return []
        
        try:
            loop = asyncio.get_event_loop()
            folder_name = folder or "INBOX"
            
            # Select folder
            await loop.run_in_executor(None, lambda: self._imap.select(folder_name))
            
            # Build search criteria
            # For Gmail, we can search by date more precisely
            search_criteria = []
            if unread_only:
                search_criteria.append("UNSEEN")
            if since:
                # IMAP SINCE uses date only, but we can filter by time after fetching
                # Use SINCE for date filtering
                search_criteria.append(f'SINCE {since.strftime("%d-%b-%Y")}')
            
            # Gmail supports searching for important emails using the \Important flag
            # But we'll fetch all and filter by importance after parsing headers
            search_query = " ".join(search_criteria) if search_criteria else "ALL"
            
            # Search for emails
            status, messages = await loop.run_in_executor(
                None,
                lambda: self._imap.search(None, search_query)
            )
            
            if status != "OK":
                logger.error("Failed to search Gmail")
                return []
            
            # Get email IDs
            email_ids = messages[0].split()[:limit]
            
            # Fetch emails with flags to check for IMPORTANT flag
            unified_emails = []
            for email_id in email_ids:
                try:
                    # Fetch both the email and its flags
                    status, msg_data = await loop.run_in_executor(
                        None,
                        lambda eid=email_id: self._imap.fetch(eid, "(RFC822 FLAGS)")
                    )
                    
                    if status == "OK" and msg_data[0]:
                        raw_email = msg_data[0][1]
                        email_message = email.message_from_bytes(raw_email)
                        
                        # Check flags for \Important
                        flags_str = ""
                        if len(msg_data[0]) > 1:
                            flags_data = msg_data[0][1] if isinstance(msg_data[0][1], bytes) else str(msg_data[0][1])
                            if b"FLAGS" in flags_data or "FLAGS" in str(flags_data):
                                # Extract flags
                                flags_part = msg_data[0][0].decode() if isinstance(msg_data[0][0], bytes) else str(msg_data[0][0])
                                if "\\Important" in flags_part or "IMPORTANT" in flags_part.upper():
                                    # Mark as important in raw data
                                    email_message["X-IMAP-Important"] = "true"
                        
                        unified_email = self._convert_imap_email(email_message, email_id.decode())
                        unified_emails.append(unified_email)
                except Exception as e:
                    logger.warning(f"Failed to fetch email {email_id}: {e}")
                    continue
            
            return unified_emails
        except Exception as e:
            logger.error(f"Error fetching Gmail emails: {e}")
            return []
    
    @with_error_boundary("Failed to send Gmail email")
    @with_logging()
    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> UnifiedEmail:
        """
        Send an email via Gmail.
        
        Note: IMAP doesn't support sending - this would require SMTP
        or Gmail API. This is a stub implementation.
        """
        logger.warning("Gmail send_email via IMAP is not supported - use SMTP or Gmail API")
        raise NotImplementedError("Gmail send_email requires SMTP or Gmail API (not implemented in IMAP connector)")
    
    @with_error_boundary("Failed to search Gmail emails", return_on_error=[])
    @with_logging()
    async def search_emails(
        self,
        query: str,
        limit: int = 50,
    ) -> List[UnifiedEmail]:
        """
        Search emails using Gmail search syntax.
        
        Args:
            query: Gmail search query (e.g., "from:example@gmail.com subject:test")
            limit: Maximum number of results
        """
        if not self._connected or not self._imap:
            logger.error("Gmail connector not connected")
            return []
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self._imap.select("INBOX"))
            
            # Gmail IMAP search
            status, messages = await loop.run_in_executor(
                None,
                lambda: self._imap.search(None, query)
            )
            
            if status != "OK":
                return []
            
            email_ids = messages[0].split()[:limit]
            unified_emails = []
            
            for email_id in email_ids:
                try:
                    status, msg_data = await loop.run_in_executor(
                        None,
                        lambda eid=email_id: self._imap.fetch(eid, "(RFC822)")
                    )
                    
                    if status == "OK" and msg_data[0]:
                        raw_email = msg_data[0][1]
                        email_message = email.message_from_bytes(raw_email)
                        unified_email = self._convert_imap_email(email_message, email_id.decode())
                        unified_emails.append(unified_email)
                except Exception as e:
                    logger.warning(f"Failed to fetch email {email_id}: {e}")
                    continue
            
            return unified_emails
        except Exception as e:
            logger.error(f"Error searching Gmail emails: {e}")
            return []
    
    @with_error_boundary("Failed to get Gmail folders", return_on_error=[])
    @with_logging()
    async def get_mailbox_folders(self) -> List[Dict[str, Any]]:
        """Get list of Gmail mailbox folders."""
        if not self._connected or not self._imap:
            logger.error("Gmail connector not connected")
            return []
        
        try:
            loop = asyncio.get_event_loop()
            status, folders = await loop.run_in_executor(
                None,
                lambda: self._imap.list()
            )
            
            if status != "OK":
                return []
            
            # Parse folder list
            folder_list = []
            for folder in folders:
                folder_str = folder.decode()
                # Parse IMAP folder format
                parts = folder_str.split(' "/" ')
                if len(parts) > 1:
                    folder_name = parts[1].strip('"')
                    folder_list.append({"id": folder_name, "name": folder_name})
            
            return folder_list
        except Exception as e:
            logger.error(f"Error getting Gmail folders: {e}")
            return []
    
    async def subscribe_to_new_mail(
        self,
        callback: Callable[[UnifiedEmail], None],
    ) -> None:
        """
        Subscribe to new email notifications.
        
        In a real implementation, this would set up IMAP IDLE
        or polling mechanisms.
        """
        self._event_callbacks.append(callback)
        logger.info(f"Subscribed callback to Gmail new mail (total callbacks: {len(self._event_callbacks)})")
        
        # Stub: In real implementation, set up IMAP IDLE or polling
        logger.warning("Gmail new mail subscription is a stub - implement IMAP IDLE or polling")
    
    def get_capabilities(self) -> ConnectorCapabilities:
        """Get Gmail connector capabilities."""
        return ConnectorCapabilities(
            can_send=False,  # IMAP doesn't support sending
            can_receive=True,
            can_search=True,
            can_archive=True,
            can_delete=True,
            supports_attachments=True,
            supports_reactions=False,
            supports_threading=True,
            supports_read_receipts=False,
        )
    
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self._connected
    
    def _convert_imap_email(self, email_message: email.message.Message, email_id: str) -> UnifiedEmail:
        """
        Convert IMAP email message to UnifiedEmail.
        
        Args:
            email_message: Python email.message.Message object
            email_id: Email ID from IMAP
        """
        # Decode subject
        subject, encoding = decode_header(email_message["Subject"])[0] if email_message["Subject"] else ("", None)
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")
        
        # Decode from address
        from_header = email_message["From"]
        from_name, from_email = email.utils.parseaddr(from_header)
        
        # Parse date
        date_str = email_message["Date"]
        try:
            timestamp = datetime(*email.utils.parsedate(date_str)[:6])
        except:
            timestamp = datetime.utcnow()
        
        # Get body
        body_text = ""
        body_html = None
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body_text = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                elif content_type == "text/html":
                    body_html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
        else:
            body_text = email_message.get_payload(decode=True).decode("utf-8", errors="ignore")
        
        # Parse recipients
        to_addresses = []
        for addr in email.utils.getaddresses(email_message.get_all("To", [])):
            to_addresses.append({"email": addr[1], "name": addr[0]})
        
        cc_addresses = []
        for addr in email.utils.getaddresses(email_message.get_all("Cc", [])):
            cc_addresses.append({"email": addr[1], "name": addr[0]})
        
        # Check for importance/priority
        # Gmail uses X-Gmail-Labels which may contain "Important"
        gmail_labels = email_message.get("X-Gmail-Labels", "")
        is_important = "Important" in gmail_labels or "\\Important" in gmail_labels
        
        # Also check X-Priority header (1 = high, 3 = normal, 5 = low)
        x_priority = email_message.get("X-Priority", "")
        priority_value = EmailPriority.NORMAL
        if x_priority:
            try:
                priority_num = int(x_priority)
                if priority_num == 1:
                    priority_value = EmailPriority.HIGH
                    is_important = True
                elif priority_num == 5:
                    priority_value = EmailPriority.LOW
            except:
                pass
        
        # Check Importance header (some clients use this)
        importance_header = email_message.get("Importance", "").lower()
        if importance_header in ["high", "urgent"]:
            priority_value = EmailPriority.HIGH
            is_important = True
        
        return UnifiedEmail(
            id=f"gmail_{email_id}",
            source_type=SourceType.GMAIL,
            source_id=email_id,
            subject=subject or "",
            body_text=body_text,
            body_html=body_html,
            from_address={"email": from_email, "name": from_name},
            to_addresses=to_addresses,
            cc_addresses=cc_addresses,
            timestamp=timestamp,
            is_read="UNSEEN" not in gmail_labels,
            is_important=is_important,
            priority=priority_value,
            raw_data={"headers": dict(email_message.items())},
        )

