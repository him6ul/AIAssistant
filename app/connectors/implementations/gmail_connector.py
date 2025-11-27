"""
Gmail connector implementation using Google Gmail API.
"""

import os
import email
import imaplib
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
        """Connect to Gmail via IMAP using synchronous imaplib in executor."""
        try:
            logger.info("=" * 80)
            logger.info("🔌 GMAIL CONNECTOR: Starting connection (IMAP in executor)...")
            logger.info(f"   Server: {self.imap_server}:{self.imap_port}")
            logger.info(f"   Username: {self.username}")
            logger.info(f"   Password: {'SET' if self.password else 'NOT SET'}")
            
            if not self.username or not self.password:
                logger.error("❌ Gmail credentials not configured")
                return False
            
            # Use synchronous imaplib in executor to avoid hanging issues
            logger.info("   Establishing SSL connection to IMAP server...")
            loop = asyncio.get_event_loop()
            
            def _connect():
                """Connect synchronously in executor thread."""
                imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                imap.login(self.username, self.password)
                return imap
            
            try:
                self._imap = await asyncio.wait_for(
                    loop.run_in_executor(None, _connect),
                    timeout=15.0
                )
                logger.info("   ✅ SSL connection established")
                logger.info("   ✅ Authentication successful")
                self._connected = True
                logger.info("✅ Gmail connector connected successfully")
                logger.info("=" * 80)
                return True
            except asyncio.TimeoutError:
                logger.error("   ❌ TIMEOUT: Connection timed out (15s limit)")
                self._imap = None
                return False
        except Exception as e:
            logger.error(f"❌ Error connecting to Gmail: {e}", exc_info=True)
            self._imap = None
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Gmail IMAP."""
        if self._imap:
            try:
                loop = asyncio.get_event_loop()
                await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self._imap.logout()),
                    timeout=5.0
                )
            except Exception as e:
                logger.warning(f"Error during logout: {e}")
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
        fetch_start = datetime.utcnow()
        logger.info("=" * 80)
        logger.info("📬 GMAIL CONNECTOR: Starting email fetch...")
        logger.info(f"   Parameters:")
        logger.info(f"     - Limit: {limit}")
        folder_display = folder or "INBOX (default)"
        logger.info(f"     - Folder: {folder_display}")
        logger.info(f"     - Unread only: {unread_only}")
        since_display = since.strftime('%Y-%m-%d %H:%M:%S UTC') if since else 'None (all emails)'
        logger.info(f"     - Since: {since_display}")
        
        # Always create a fresh connection for each fetch to avoid stale connection issues
        # The connection reuse was causing hangs with stale connections
        logger.info("   🔌 Creating fresh connection for this fetch...")
        if self._imap:
            # Try to close existing connection gracefully, but don't wait if it hangs
            try:
                loop = asyncio.get_event_loop()
                await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self._imap.logout() if self._imap else None),
                    timeout=2.0
                )
            except:
                pass  # Ignore errors when closing stale connection
            self._imap = None
            self._connected = False
        
        connect_success = await self.connect()
        if not connect_success:
            logger.error("   ❌ Failed to connect")
            return []
        
        try:
            folder_name = folder or "INBOX"
            
            # Select folder with timeout (run in executor to avoid hanging)
            logger.info(f"   Selecting folder: {folder_name}")
            select_start = datetime.utcnow()
            try:
                # Run select in executor using synchronous imaplib
                def _select_folder():
                    """Select folder synchronously in executor thread."""
                    status, data = self._imap.select(folder_name)
                    return status
                
                loop = asyncio.get_event_loop()
                status = await asyncio.wait_for(
                    loop.run_in_executor(None, _select_folder),
                    timeout=10.0
                )
                select_duration = (datetime.utcnow() - select_start).total_seconds()
                logger.info(f"   ✅ Folder selected: {status} (took {select_duration:.2f}s)")
            except asyncio.TimeoutError:
                select_duration = (datetime.utcnow() - select_start).total_seconds()
                logger.error(f"   ❌ TIMEOUT: Selecting folder {folder_name} timed out after {select_duration:.2f}s (10s limit)")
                return []
            except Exception as select_error:
                select_duration = (datetime.utcnow() - select_start).total_seconds()
                logger.error(f"   ❌ Error selecting folder {folder_name} after {select_duration:.2f}s: {select_error}", exc_info=True)
                return []
            
            # Build search criteria
            # For Gmail, we can search by date more precisely
            search_criteria = []
            if unread_only:
                search_criteria.append("UNSEEN")
                logger.info("   🔍 Search filter: UNSEEN (unread emails only)")
            if since:
                # IMAP SINCE uses date only, but we can filter by time after fetching
                # Use SINCE for date filtering
                since_str = since.strftime("%d-%b-%Y")
                search_criteria.append(f'SINCE {since_str}')
                logger.info(f"   🔍 Search filter: SINCE {since_str}")
            
            # Gmail supports searching for important emails using the \Important flag
            # But we'll fetch all and filter by importance after parsing headers
            search_query = " ".join(search_criteria) if search_criteria else "ALL"
            logger.info(f"   🔍 IMAP search query: '{search_query}'")
            
            # Search for emails (run in executor to avoid hanging)
            logger.info("   Searching for emails...")
            search_start = datetime.utcnow()
            try:
                # Run search in executor using synchronous imaplib
                def _search_emails():
                    """Search emails synchronously in executor thread."""
                    status, messages = self._imap.search(None, search_query)
                    return status, messages
                
                loop = asyncio.get_event_loop()
                status, messages = await asyncio.wait_for(
                    loop.run_in_executor(None, _search_emails),
                    timeout=10.0
                )
                search_duration = (datetime.utcnow() - search_start).total_seconds()
            except asyncio.TimeoutError:
                search_duration = (datetime.utcnow() - search_start).total_seconds()
                logger.error(f"   ❌ TIMEOUT: Search timed out after {search_duration:.2f}s (10s limit)")
                return []
            except Exception as search_error:
                logger.error(f"   ❌ Error during search: {search_error}", exc_info=True)
                return []
            
            if status != "OK":
                logger.error(f"   ❌ Failed to search Gmail (status: {status})")
                return []
            
            # Get email IDs from imaplib response
            if not messages or len(messages) == 0:
                logger.info("   ℹ️  No emails found matching search criteria")
                return []
            
            # imaplib returns messages as list of bytes
            email_ids_str = messages[0].decode('utf-8', errors='ignore') if isinstance(messages[0], bytes) else str(messages[0])
            
            if not email_ids_str or not email_ids_str.strip():
                logger.info("   ℹ️  No emails found matching search criteria")
                return []
            
            all_email_ids = email_ids_str.split()
            total_found = len(all_email_ids)
            email_ids = all_email_ids[:limit]
            
            logger.info(f"   ✅ Search completed in {search_duration:.2f}s")
            logger.info(f"   📊 Found {total_found} total email(s) matching criteria")
            logger.info(f"   📊 Will fetch {len(email_ids)} email(s) (limited to {limit})")
            
            # Fetch emails with flags to check for IMPORTANT flag
            unified_emails = []
            fetch_count = 0
            error_count = 0
            
            logger.info("   📥 Fetching individual emails...")
            for idx, email_id in enumerate(email_ids, 1):
                try:
                    email_id_str = email_id.decode() if isinstance(email_id, bytes) else str(email_id)
                    logger.debug(f"   [{idx}/{len(email_ids)}] Fetching email ID: {email_id_str}")
                    
                    # Fetch both the email and its flags (run in executor to avoid hanging)
                    def _fetch_email():
                        """Fetch email synchronously in executor thread."""
                        status, msg_data = self._imap.fetch(email_id_str, "(RFC822 FLAGS)")
                        return status, msg_data
                    
                    loop = asyncio.get_event_loop()
                    status, msg_data = await asyncio.wait_for(
                        loop.run_in_executor(None, _fetch_email),
                        timeout=10.0
                    )
                    
                    if status != "OK" or not msg_data or not msg_data[0]:
                        logger.warning(f"   ⚠️  Failed to fetch email {email_id_str}: status={status}")
                        error_count += 1
                        continue
                    
                    # Extract email body and flags
                    # msg_data structure: [(b'1 (RFC822 {1234}', b'email body...'), b' FLAGS (\\Seen \\Important)')]
                    raw_email = None
                    flags_str = ""
                    is_important_flag = False
                    
                    # Find the RFC822 part
                    for part in msg_data:
                        if isinstance(part, tuple) and len(part) >= 2:
                            # Check if this part contains the email body
                            if isinstance(part[1], bytes) and b"From:" in part[1]:
                                raw_email = part[1]
                            # Check for flags
                            elif isinstance(part[1], bytes) and b"FLAGS" in part[1]:
                                flags_str = part[1].decode() if isinstance(part[1], bytes) else str(part[1])
                                if "\\Important" in flags_str or "IMPORTANT" in flags_str.upper():
                                    is_important_flag = True
                                    logger.debug(f"      ✅ Found \\Important flag in IMAP flags")
                    
                    # Alternative: try to get email from first part
                    if raw_email is None and len(msg_data) > 0:
                        for item in msg_data:
                            if isinstance(item, tuple) and len(item) >= 2:
                                if isinstance(item[1], bytes) and len(item[1]) > 100:  # Likely the email body
                                    raw_email = item[1]
                                    break
                    
                    if raw_email is None:
                        logger.warning(f"   ⚠️  Could not extract email body for {email_id_str}")
                        error_count += 1
                        continue
                    
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Add important flag to headers if found
                    if is_important_flag:
                        email_message["X-IMAP-Important"] = "true"
                    
                    unified_email = self._convert_imap_email(email_message, email_id_str)
                    unified_emails.append(unified_email)
                    fetch_count += 1
                    
                    logger.debug(f"      ✅ Converted: '{unified_email.subject[:50]}...' from {unified_email.from_address.get('email', 'Unknown')}")
                    logger.debug(f"         - Important: {unified_email.is_important}, Priority: {unified_email.priority}")
                    
                except Exception as e:
                    logger.warning(f"   ⚠️  Failed to fetch email {email_id}: {e}", exc_info=True)
                    error_count += 1
                    continue
            
            fetch_duration = (datetime.utcnow() - fetch_start).total_seconds()
            logger.info("-" * 80)
            logger.info(f"📊 GMAIL FETCH SUMMARY:")
            logger.info(f"   Total found: {total_found} email(s)")
            logger.info(f"   Successfully fetched: {fetch_count} email(s)")
            logger.info(f"   Errors: {error_count} email(s)")
            logger.info(f"   Duration: {fetch_duration:.2f}s")
            logger.info("=" * 80)
            
            # Disconnect after successful fetch
            logger.info("   🔌 Disconnecting after fetch...")
            await self.disconnect()
            
            return unified_emails
        except Exception as e:
            logger.error(f"❌ Error fetching Gmail emails: {e}", exc_info=True)
            # Ensure we disconnect even on error
            try:
                await self.disconnect()
            except Exception as disconnect_error:
                logger.warning(f"   ⚠️  Error during disconnect after error: {disconnect_error}")
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
            # Use async IMAP
            await self._imap.select("INBOX")
            
            # Gmail IMAP search (async)
            result = await self._imap.search(None, query)
            status, messages = result
            
            if status != "OK":
                return []
            
            # Decode messages
            messages_str = messages[0].decode() if isinstance(messages[0], bytes) else str(messages[0])
            email_ids = messages_str.split()[:limit]
            unified_emails = []
            
            for email_id in email_ids:
                try:
                    email_id_str = email_id.decode() if isinstance(email_id, bytes) else str(email_id)
                    result = await self._imap.fetch(email_id_str, "(RFC822)")
                    status, msg_data = result
                    
                    if status == "OK" and msg_data and len(msg_data) > 0:
                        # Extract email body from msg_data
                        raw_email = None
                        for part in msg_data:
                            if isinstance(part, tuple) and len(part) >= 2:
                                if isinstance(part[1], bytes) and b"From:" in part[1]:
                                    raw_email = part[1]
                                    break
                        
                        if raw_email:
                            email_message = email.message_from_bytes(raw_email)
                            unified_email = self._convert_imap_email(email_message, email_id_str)
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
            # Use async IMAP
            result = await self._imap.list()
            status, folders = result
            
            if status != "OK":
                return []
            
            # Parse folder list
            folder_list = []
            for folder in folders:
                folder_str = folder.decode() if isinstance(folder, bytes) else str(folder)
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
        logger.debug(f"      🔄 Converting IMAP email (ID: {email_id})...")
        
        # Decode subject
        subject, encoding = decode_header(email_message["Subject"])[0] if email_message["Subject"] else ("", None)
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")
        logger.debug(f"         Subject: '{subject[:50]}{'...' if len(subject) > 50 else ''}'")
        
        # Decode from address
        from_header = email_message["From"]
        from_name, from_email = email.utils.parseaddr(from_header)
        logger.debug(f"         From: {from_name} <{from_email}>")
        
        # Parse date
        date_str = email_message["Date"]
        try:
            timestamp = datetime(*email.utils.parsedate(date_str)[:6])
            logger.debug(f"         Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        except Exception as e:
            logger.warning(f"         ⚠️  Failed to parse date '{date_str}': {e}, using current time")
            timestamp = datetime.utcnow()
        
        # Get body
        body_text = ""
        body_html = None
        
        if email_message.is_multipart():
            logger.debug(f"         Email is multipart, extracting body parts...")
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body_text = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    logger.debug(f"         Found text/plain body ({len(body_text)} chars)")
                elif content_type == "text/html":
                    body_html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    logger.debug(f"         Found text/html body ({len(body_html) if body_html else 0} chars)")
        else:
            body_text = email_message.get_payload(decode=True).decode("utf-8", errors="ignore")
            logger.debug(f"         Email is single part, extracted body ({len(body_text)} chars)")
        
        # Parse recipients
        to_addresses = []
        for addr in email.utils.getaddresses(email_message.get_all("To", [])):
            to_addresses.append({"email": addr[1], "name": addr[0]})
        
        cc_addresses = []
        for addr in email.utils.getaddresses(email_message.get_all("Cc", [])):
            cc_addresses.append({"email": addr[1], "name": addr[0]})
        
        logger.debug(f"         To: {len(to_addresses)} recipient(s), Cc: {len(cc_addresses)} recipient(s)")
        
        # Check for importance/priority
        logger.debug(f"         Checking importance indicators...")
        
        # Gmail uses X-Gmail-Labels which may contain "Important"
        gmail_labels = email_message.get("X-Gmail-Labels", "")
        is_important = "Important" in gmail_labels or "\\Important" in gmail_labels
        if is_important:
            logger.debug(f"         ✅ IMPORTANT: Found in X-Gmail-Labels: {gmail_labels}")
        
        # Check IMAP Important flag
        if email_message.get("X-IMAP-Important") == "true":
            is_important = True
            logger.debug(f"         ✅ IMPORTANT: Found \\Important IMAP flag")
        
        # Also check X-Priority header (1 = high, 3 = normal, 5 = low)
        x_priority = email_message.get("X-Priority", "")
        priority_value = EmailPriority.NORMAL
        if x_priority:
            try:
                priority_num = int(x_priority)
                if priority_num == 1:
                    priority_value = EmailPriority.HIGH
                    is_important = True
                    logger.debug(f"         ✅ HIGH PRIORITY: X-Priority = {priority_num}")
                elif priority_num == 5:
                    priority_value = EmailPriority.LOW
                    logger.debug(f"         ℹ️  LOW PRIORITY: X-Priority = {priority_num}")
            except:
                pass
        
        # Check Importance header (some clients use this)
        importance_header = email_message.get("Importance", "").lower()
        if importance_header in ["high", "urgent"]:
            priority_value = EmailPriority.HIGH
            is_important = True
            logger.debug(f"         ✅ HIGH PRIORITY: Importance header = {importance_header}")
        
        if not is_important:
            logger.debug(f"         ℹ️  Not marked as important (normal priority)")
        
        logger.debug(f"         ✅ Conversion complete: Important={is_important}, Priority={priority_value.value}")
        
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

