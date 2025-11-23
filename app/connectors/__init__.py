"""
Connector module for integrating with various communication and productivity platforms.

This module provides a pluggable architecture for connecting to:
- Messaging platforms (WhatsApp, Teams, Slack)
- Email platforms (Gmail, Outlook, IMAP)
- Notes platforms (OneNote)
- Future platforms (Telegram, SMS, Apple Mail, CRMs, etc.)

All connectors follow a unified interface pattern for easy extensibility.
"""

from app.connectors.base import (
    MessageSourceConnector,
    MailSourceConnector,
    NoteSourceConnector,
    ConnectorCapabilities,
    SourceType,
)
from app.connectors.registry import ConnectorRegistry
from app.connectors.models import (
    UnifiedMessage,
    UnifiedEmail,
    UnifiedNote,
    UnifiedMeeting,
    MessageStatus,
    EmailPriority,
)

__all__ = [
    "MessageSourceConnector",
    "MailSourceConnector",
    "NoteSourceConnector",
    "ConnectorCapabilities",
    "SourceType",
    "ConnectorRegistry",
    "UnifiedMessage",
    "UnifiedEmail",
    "UnifiedNote",
    "UnifiedMeeting",
    "MessageStatus",
    "EmailPriority",
]
