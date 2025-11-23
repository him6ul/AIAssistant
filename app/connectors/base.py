"""
Base interfaces (abstract classes) for all connector types.

These define the contract that all connectors must implement.
No provider-specific logic should be in these base classes.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
from app.connectors.models import (
    UnifiedMessage,
    UnifiedEmail,
    UnifiedNote,
    SourceType,
)


class ConnectorCapabilities:
    """Describes what capabilities a connector supports."""
    
    def __init__(
        self,
        can_send: bool = False,
        can_receive: bool = False,
        can_search: bool = False,
        can_archive: bool = False,
        can_delete: bool = False,
        supports_attachments: bool = False,
        supports_reactions: bool = False,
        supports_threading: bool = False,
        supports_read_receipts: bool = False,
    ):
        self.can_send = can_send
        self.can_receive = can_receive
        self.can_search = can_search
        self.can_archive = can_archive
        self.can_delete = can_delete
        self.supports_attachments = supports_attachments
        self.supports_reactions = supports_reactions
        self.supports_threading = supports_threading
        self.supports_read_receipts = supports_read_receipts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "can_send": self.can_send,
            "can_receive": self.can_receive,
            "can_search": self.can_search,
            "can_archive": self.can_archive,
            "can_delete": self.can_delete,
            "supports_attachments": self.supports_attachments,
            "supports_reactions": self.supports_reactions,
            "supports_threading": self.supports_threading,
            "supports_read_receipts": self.supports_read_receipts,
        }


class MessageSourceConnector(ABC):
    """
    Base interface for messaging platform connectors.
    
    Implementations: WhatsAppConnector, TeamsConnector, SlackConnector, etc.
    """
    
    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """Return the source type this connector handles."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the messaging platform.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the messaging platform."""
        pass
    
    @abstractmethod
    async def fetch_messages(
        self,
        limit: int = 50,
        since: Optional[datetime] = None,
        thread_id: Optional[str] = None,
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from the platform.
        
        Args:
            limit: Maximum number of messages to fetch
            since: Only fetch messages after this timestamp
            thread_id: Fetch messages from specific thread/conversation
        
        Returns:
            List of UnifiedMessage objects
        """
        pass
    
    @abstractmethod
    async def send_message(
        self,
        content: str,
        to_user_id: str,
        thread_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> UnifiedMessage:
        """
        Send a message through the platform.
        
        Args:
            content: Message content
            to_user_id: Recipient user ID
            thread_id: Optional thread/conversation ID
            attachments: Optional list of attachments
        
        Returns:
            UnifiedMessage object representing the sent message
        """
        pass
    
    @abstractmethod
    async def subscribe_to_events(
        self,
        callback: Callable[[UnifiedMessage], None],
    ) -> None:
        """
        Subscribe to real-time message events.
        
        Args:
            callback: Function to call when new message arrives
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> ConnectorCapabilities:
        """
        Get the capabilities of this connector.
        
        Returns:
            ConnectorCapabilities object
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connector is currently connected."""
        pass


class MailSourceConnector(ABC):
    """
    Base interface for email platform connectors.
    
    Implementations: GmailConnector, OutlookConnector, IMAPConnector, etc.
    """
    
    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """Return the source type this connector handles."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the email platform.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the email platform."""
        pass
    
    @abstractmethod
    async def fetch_emails(
        self,
        limit: int = 50,
        folder: Optional[str] = None,
        unread_only: bool = False,
        since: Optional[datetime] = None,
    ) -> List[UnifiedEmail]:
        """
        Fetch emails from the platform.
        
        Args:
            limit: Maximum number of emails to fetch
            folder: Specific folder to fetch from (inbox, sent, etc.)
            unread_only: Only fetch unread emails
            since: Only fetch emails after this timestamp
        
        Returns:
            List of UnifiedEmail objects
        """
        pass
    
    @abstractmethod
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
        Send an email through the platform.
        
        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
            cc_addresses: Optional CC addresses
            bcc_addresses: Optional BCC addresses
            attachments: Optional list of attachments
        
        Returns:
            UnifiedEmail object representing the sent email
        """
        pass
    
    @abstractmethod
    async def search_emails(
        self,
        query: str,
        limit: int = 50,
    ) -> List[UnifiedEmail]:
        """
        Search emails using platform-specific query syntax.
        
        Args:
            query: Search query string
            limit: Maximum number of results
        
        Returns:
            List of UnifiedEmail objects matching the query
        """
        pass
    
    @abstractmethod
    async def get_mailbox_folders(self) -> List[Dict[str, Any]]:
        """
        Get list of available mailbox folders.
        
        Returns:
            List of folder dictionaries with id, name, etc.
        """
        pass
    
    @abstractmethod
    async def subscribe_to_new_mail(
        self,
        callback: Callable[[UnifiedEmail], None],
    ) -> None:
        """
        Subscribe to new email notifications.
        
        Args:
            callback: Function to call when new email arrives
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> ConnectorCapabilities:
        """
        Get the capabilities of this connector.
        
        Returns:
            ConnectorCapabilities object
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connector is currently connected."""
        pass


class NoteSourceConnector(ABC):
    """
    Base interface for notes platform connectors.
    
    Implementations: OneNoteConnector, etc.
    """
    
    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """Return the source type this connector handles."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the notes platform.
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the notes platform."""
        pass
    
    @abstractmethod
    async def fetch_notes(
        self,
        limit: int = 50,
        notebook_id: Optional[str] = None,
        section_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[UnifiedNote]:
        """
        Fetch notes from the platform.
        
        Args:
            limit: Maximum number of notes to fetch
            notebook_id: Optional notebook ID to filter by
            section_id: Optional section ID to filter by
            since: Only fetch notes updated after this timestamp
        
        Returns:
            List of UnifiedNote objects
        """
        pass
    
    @abstractmethod
    async def create_note(
        self,
        title: str,
        content: str,
        notebook_id: Optional[str] = None,
        section_id: Optional[str] = None,
        content_html: Optional[str] = None,
    ) -> UnifiedNote:
        """
        Create a new note.
        
        Args:
            title: Note title
            content: Note content (plain text)
            notebook_id: Optional notebook ID
            section_id: Optional section ID
            content_html: Optional HTML content
        
        Returns:
            UnifiedNote object representing the created note
        """
        pass
    
    @abstractmethod
    async def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        content_html: Optional[str] = None,
    ) -> UnifiedNote:
        """
        Update an existing note.
        
        Args:
            note_id: ID of note to update
            title: Optional new title
            content: Optional new content (plain text)
            content_html: Optional new HTML content
        
        Returns:
            Updated UnifiedNote object
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> ConnectorCapabilities:
        """
        Get the capabilities of this connector.
        
        Returns:
            ConnectorCapabilities object
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connector is currently connected."""
        pass
