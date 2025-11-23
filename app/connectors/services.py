"""
Unified services that aggregate data from all connectors.

These services provide a single interface to access messages, emails, and notes
from all registered connectors, regardless of the underlying platform.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from app.connectors.registry import get_registry
from app.connectors.models import (
    UnifiedMessage,
    UnifiedEmail,
    UnifiedNote,
    SourceType,
)
from app.connectors.base import (
    MessageSourceConnector,
    MailSourceConnector,
    NoteSourceConnector,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UnifiedMessageService:
    """
    Unified service for accessing messages from all messaging connectors.
    
    This service aggregates messages from Slack, Telegram, SMS, etc.
    and provides a single interface to access them.
    """
    
    def __init__(self, registry=None):
        """
        Initialize unified message service.
        
        Args:
            registry: ConnectorRegistry instance (uses global if None)
        """
        self.registry = registry or get_registry()
    
    async def get_all_messages(
        self,
        limit: int = 50,
        source_types: Optional[List[SourceType]] = None,
        since: Optional[datetime] = None,
    ) -> List[UnifiedMessage]:
        """
        Get messages from all registered messaging connectors.
        
        Args:
            limit: Maximum number of messages per connector
            source_types: Optional list of source types to filter by
            since: Only fetch messages after this timestamp
        
        Returns:
            List of UnifiedMessage objects from all connectors
        """
        all_messages = []
        connectors = self.registry.get_all_message_connectors()
        
        if source_types:
            connectors = {
                st: conn for st, conn in connectors.items()
                if st in source_types
            }
        
        for source_type, connector in connectors.items():
            try:
                if not connector.is_connected():
                    logger.warning(f"Connector {source_type} is not connected, skipping")
                    continue
                
                messages = await connector.fetch_messages(
                    limit=limit,
                    since=since,
                )
                all_messages.extend(messages)
                logger.debug(f"Fetched {len(messages)} messages from {source_type}")
            except Exception as e:
                logger.error(f"Error fetching messages from {source_type}: {e}", exc_info=True)
                # Continue with other connectors - graceful degradation
        
        # Sort by timestamp (newest first)
        all_messages.sort(key=lambda m: m.timestamp, reverse=True)
        
        return all_messages
    
    async def send_message(
        self,
        content: str,
        to_user_id: str,
        source_type: SourceType,
        thread_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> UnifiedMessage:
        """
        Send a message through a specific connector.
        
        Args:
            content: Message content
            to_user_id: Recipient user ID
            source_type: Source type to send through
            thread_id: Optional thread/conversation ID
            attachments: Optional attachments
        
        Returns:
            UnifiedMessage object representing the sent message
        """
        connector = self.registry.get_message_connector(source_type)
        if not connector:
            raise ValueError(f"No message connector registered for {source_type}")
        
        if not connector.is_connected():
            raise RuntimeError(f"Connector {source_type} is not connected")
        
        return await connector.send_message(
            content=content,
            to_user_id=to_user_id,
            thread_id=thread_id,
            attachments=attachments,
        )
    
    async def search_messages(
        self,
        query: str,
        source_types: Optional[List[SourceType]] = None,
        limit: int = 50,
    ) -> List[UnifiedMessage]:
        """
        Search messages across all connectors.
        
        Note: This is a simple text search. Advanced search would require
        connector-specific implementations.
        
        Args:
            query: Search query string
            source_types: Optional list of source types to search
            limit: Maximum number of results
        
        Returns:
            List of UnifiedMessage objects matching the query
        """
        # Get all messages and filter by query
        all_messages = await self.get_all_messages(
            limit=limit * 2,  # Get more to filter
            source_types=source_types,
        )
        
        # Simple text search (case-insensitive)
        query_lower = query.lower()
        matching_messages = [
            msg for msg in all_messages
            if query_lower in msg.content.lower() or
               query_lower in (msg.from_user.get("name", "") or "").lower()
        ]
        
        return matching_messages[:limit]


class UnifiedInboxService:
    """
    Unified service for accessing emails from all mail connectors.
    
    This service aggregates emails from Gmail, Outlook, IMAP, etc.
    and provides a single interface to access them.
    """
    
    def __init__(self, registry=None):
        """
        Initialize unified inbox service.
        
        Args:
            registry: ConnectorRegistry instance (uses global if None)
        """
        self.registry = registry or get_registry()
    
    async def get_all_emails(
        self,
        limit: int = 50,
        source_types: Optional[List[SourceType]] = None,
        folder: Optional[str] = None,
        unread_only: bool = False,
        since: Optional[datetime] = None,
    ) -> List[UnifiedEmail]:
        """
        Get emails from all registered mail connectors.
        
        Args:
            limit: Maximum number of emails per connector
            source_types: Optional list of source types to filter by
            folder: Optional folder name (inbox, sent, etc.)
            unread_only: Only fetch unread emails
            since: Only fetch emails after this timestamp
        
        Returns:
            List of UnifiedEmail objects from all connectors
        """
        all_emails = []
        connectors = self.registry.get_all_mail_connectors()
        
        logger.info(f"📬 UnifiedInboxService: Fetching emails from {len(connectors)} registered mail connector(s)")
        
        if source_types:
            connectors = {
                st: conn for st, conn in connectors.items()
                if st in source_types
            }
            logger.info(f"   Filtered to {len(connectors)} connector(s) matching source types: {[st.value for st in source_types]}")
        
        for source_type, connector in connectors.items():
            try:
                logger.info(f"   🔍 Checking {source_type.value} connector...")
                
                if not connector.is_connected():
                    logger.warning(f"   ⚠️  {source_type.value} connector is not connected, skipping")
                    continue
                
                logger.info(f"   ✅ {source_type.value} is connected, fetching emails (limit={limit}, unread_only={unread_only}, since={since})...")
                fetch_start = datetime.utcnow()
                
                emails = await connector.fetch_emails(
                    limit=limit,
                    folder=folder,
                    unread_only=unread_only,
                    since=since,
                )
                
                fetch_duration = (datetime.utcnow() - fetch_start).total_seconds()
                all_emails.extend(emails)
                logger.info(f"   ✅ Fetched {len(emails)} emails from {source_type.value} in {fetch_duration:.2f}s")
                
            except Exception as e:
                logger.error(f"   ❌ Error fetching emails from {source_type.value}: {e}", exc_info=True)
                # Continue with other connectors - graceful degradation
        
        # Sort by timestamp (newest first)
        all_emails.sort(key=lambda e: e.timestamp, reverse=True)
        
        logger.info(f"📊 UnifiedInboxService: Total {len(all_emails)} emails fetched from all sources")
        
        return all_emails
    
    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        body_text: str,
        source_type: SourceType,
        body_html: Optional[str] = None,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> UnifiedEmail:
        """
        Send an email through a specific connector.
        
        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            source_type: Source type to send through
            body_html: Optional HTML body
            cc_addresses: Optional CC addresses
            bcc_addresses: Optional BCC addresses
            attachments: Optional attachments
        
        Returns:
            UnifiedEmail object representing the sent email
        """
        connector = self.registry.get_mail_connector(source_type)
        if not connector:
            raise ValueError(f"No mail connector registered for {source_type}")
        
        if not connector.is_connected():
            raise RuntimeError(f"Connector {source_type} is not connected")
        
        return await connector.send_email(
            to_addresses=to_addresses,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            cc_addresses=cc_addresses,
            bcc_addresses=bcc_addresses,
            attachments=attachments,
        )
    
    async def search_emails(
        self,
        query: str,
        source_types: Optional[List[SourceType]] = None,
        limit: int = 50,
    ) -> List[UnifiedEmail]:
        """
        Search emails across all connectors.
        
        Args:
            query: Search query string
            source_types: Optional list of source types to search
            limit: Maximum number of results per connector
        
        Returns:
            List of UnifiedEmail objects matching the query
        """
        all_emails = []
        connectors = self.registry.get_all_mail_connectors()
        
        if source_types:
            connectors = {
                st: conn for st, conn in connectors.items()
                if st in source_types
            }
        
        for source_type, connector in connectors.items():
            try:
                if not connector.is_connected():
                    continue
                
                # Use connector's native search if available
                if connector.get_capabilities().can_search:
                    emails = await connector.search_emails(query=query, limit=limit)
                    all_emails.extend(emails)
                else:
                    # Fallback to fetching and filtering
                    emails = await connector.fetch_emails(limit=limit * 2)
                    query_lower = query.lower()
                    matching = [
                        e for e in emails
                        if query_lower in e.subject.lower() or
                           query_lower in e.body_text.lower()
                    ]
                    all_emails.extend(matching[:limit])
            except Exception as e:
                logger.error(f"Error searching emails from {source_type}: {e}", exc_info=True)
        
        # Sort by timestamp (newest first)
        all_emails.sort(key=lambda e: e.timestamp, reverse=True)
        
        return all_emails[:limit]


class UnifiedNotesService:
    """
    Unified service for accessing notes from all notes connectors.
    
    This service aggregates notes from OneNote, etc.
    and provides a single interface to access them.
    """
    
    def __init__(self, registry=None):
        """
        Initialize unified notes service.
        
        Args:
            registry: ConnectorRegistry instance (uses global if None)
        """
        self.registry = registry or get_registry()
    
    async def get_all_notes(
        self,
        limit: int = 50,
        source_types: Optional[List[SourceType]] = None,
        since: Optional[datetime] = None,
    ) -> List[UnifiedNote]:
        """
        Get notes from all registered notes connectors.
        
        Args:
            limit: Maximum number of notes per connector
            source_types: Optional list of source types to filter by
            since: Only fetch notes updated after this timestamp
        
        Returns:
            List of UnifiedNote objects from all connectors
        """
        all_notes = []
        connectors = self.registry.get_all_note_connectors()
        
        if source_types:
            connectors = {
                st: conn for st, conn in connectors.items()
                if st in source_types
            }
        
        for source_type, connector in connectors.items():
            try:
                if not connector.is_connected():
                    logger.warning(f"Connector {source_type} is not connected, skipping")
                    continue
                
                notes = await connector.fetch_notes(
                    limit=limit,
                    since=since,
                )
                all_notes.extend(notes)
                logger.debug(f"Fetched {len(notes)} notes from {source_type}")
            except Exception as e:
                logger.error(f"Error fetching notes from {source_type}: {e}", exc_info=True)
                # Continue with other connectors - graceful degradation
        
        # Sort by updated_at (newest first)
        all_notes.sort(key=lambda n: n.updated_at, reverse=True)
        
        return all_notes
    
    async def create_note(
        self,
        title: str,
        content: str,
        source_type: SourceType,
        content_html: Optional[str] = None,
        notebook_id: Optional[str] = None,
        section_id: Optional[str] = None,
    ) -> UnifiedNote:
        """
        Create a note through a specific connector.
        
        Args:
            title: Note title
            content: Note content (plain text)
            source_type: Source type to create in
            content_html: Optional HTML content
            notebook_id: Optional notebook ID
            section_id: Optional section ID
        
        Returns:
            UnifiedNote object representing the created note
        """
        connector = self.registry.get_note_connector(source_type)
        if not connector:
            raise ValueError(f"No note connector registered for {source_type}")
        
        if not connector.is_connected():
            raise RuntimeError(f"Connector {source_type} is not connected")
        
        return await connector.create_note(
            title=title,
            content=content,
            content_html=content_html,
            notebook_id=notebook_id,
            section_id=section_id,
        )

