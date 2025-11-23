"""
Unified data models for all connector types.

These models provide a common schema that all connectors must map to,
ensuring consistent data representation across different platforms.
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Enumeration of all supported source types."""
    WHATSAPP = "whatsapp"
    TEAMS = "teams"
    SLACK = "slack"
    OUTLOOK = "outlook"
    GMAIL = "gmail"
    IMAP = "imap"
    ONENOTE = "onenote"
    TELEGRAM = "telegram"
    SMS = "sms"
    APPLE_MAIL = "apple_mail"
    CUSTOM = "custom"


class MessageStatus(str, Enum):
    """Message delivery/read status."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"


class EmailPriority(str, Enum):
    """Email priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class UnifiedMessage:
    """
    Unified message model for all messaging platforms.
    
    All messaging connectors (WhatsApp, Teams, Slack, etc.) must
    convert their native message format to this unified model.
    """
    # Required fields (must come first)
    id: str
    source_type: SourceType
    source_id: str  # Original ID from the source platform
    content: str
    from_user: Dict[str, Any]  # {id, name, email, phone, etc.}
    
    # Optional fields (must come after required fields)
    thread_id: Optional[str] = None
    conversation_id: Optional[str] = None
    content_type: str = "text"  # text, image, video, audio, file, etc.
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    to_users: List[Dict[str, Any]] = field(default_factory=list)
    cc_users: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    edited_at: Optional[datetime] = None
    status: MessageStatus = MessageStatus.SENT
    is_read: bool = False
    is_important: bool = False
    is_archived: bool = False
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "thread_id": self.thread_id,
            "conversation_id": self.conversation_id,
            "content": self.content,
            "content_type": self.content_type,
            "attachments": self.attachments,
            "from_user": self.from_user,
            "to_users": self.to_users,
            "cc_users": self.cc_users,
            "timestamp": self.timestamp.isoformat(),
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
            "status": self.status.value,
            "is_read": self.is_read,
            "is_important": self.is_important,
            "is_archived": self.is_archived,
            "raw_data": self.raw_data,
        }


@dataclass
class UnifiedEmail:
    """
    Unified email model for all email platforms.
    
    All email connectors (Gmail, Outlook, IMAP, etc.) must
    convert their native email format to this unified model.
    """
    # Required fields
    id: str
    source_type: SourceType
    source_id: str  # Original ID from the source platform
    subject: str
    body_text: str
    from_address: Dict[str, Any]  # {email, name}
    
    # Optional fields
    body_html: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    to_addresses: List[Dict[str, Any]] = field(default_factory=list)
    cc_addresses: List[Dict[str, Any]] = field(default_factory=list)
    bcc_addresses: List[Dict[str, Any]] = field(default_factory=list)
    reply_to: Optional[Dict[str, Any]] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    received_at: Optional[datetime] = None
    is_read: bool = False
    is_starred: bool = False
    is_important: bool = False
    priority: EmailPriority = EmailPriority.NORMAL
    folder: Optional[str] = None  # inbox, sent, drafts, spam, etc.
    labels: List[str] = field(default_factory=list)
    thread_id: Optional[str] = None
    
    # Platform-specific metadata
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "subject": self.subject,
            "body_text": self.body_text,
            "body_html": self.body_html,
            "attachments": self.attachments,
            "from_address": self.from_address,
            "to_addresses": self.to_addresses,
            "cc_addresses": self.cc_addresses,
            "bcc_addresses": self.bcc_addresses,
            "reply_to": self.reply_to,
            "timestamp": self.timestamp.isoformat(),
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "is_read": self.is_read,
            "is_starred": self.is_starred,
            "is_important": self.is_important,
            "priority": self.priority.value,
            "folder": self.folder,
            "labels": self.labels,
            "thread_id": self.thread_id,
            "raw_data": self.raw_data,
        }


@dataclass
class UnifiedNote:
    """
    Unified note model for all notes platforms.
    
    All notes connectors (OneNote, etc.) must convert their
    native note format to this unified model.
    """
    id: str
    source_type: SourceType
    source_id: str  # Original ID from the source platform
    
    # Content
    title: str
    content: str
    content_html: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    
    # Organization
    notebook_id: Optional[str] = None
    notebook_name: Optional[str] = None
    section_id: Optional[str] = None
    section_name: Optional[str] = None
    page_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    is_favorite: bool = False
    
    # Platform-specific metadata
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "title": self.title,
            "content": self.content,
            "content_html": self.content_html,
            "attachments": self.attachments,
            "notebook_id": self.notebook_id,
            "notebook_name": self.notebook_name,
            "section_id": self.section_id,
            "section_name": self.section_name,
            "page_id": self.page_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "tags": self.tags,
            "is_favorite": self.is_favorite,
            "raw_data": self.raw_data,
        }


@dataclass
class UnifiedMeeting:
    """
    Unified meeting/calendar event model.
    
    For calendar integrations (Outlook Calendar, Google Calendar, etc.)
    """
    # Required fields
    id: str
    source_type: SourceType
    source_id: str
    title: str
    start_time: datetime
    end_time: datetime
    
    # Optional fields
    description: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    is_all_day: bool = False
    organizer: Dict[str, Any] = field(default_factory=dict)
    attendees: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    status: str = "confirmed"  # confirmed, tentative, cancelled
    recurrence: Optional[Dict[str, Any]] = None
    reminders: List[Dict[str, Any]] = field(default_factory=list)
    
    # Platform-specific metadata
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_type": self.source_type.value,
            "source_id": self.source_id,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "timezone": self.timezone,
            "is_all_day": self.is_all_day,
            "organizer": self.organizer,
            "attendees": self.attendees,
            "status": self.status,
            "recurrence": self.recurrence,
            "reminders": self.reminders,
            "raw_data": self.raw_data,
        }

