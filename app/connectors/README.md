# Connector Architecture

A modular, pluggable architecture for integrating with multiple communication and productivity platforms.

## 🎯 Overview

This module provides a clean, extensible system for connecting to various platforms:
- **Messaging**: WhatsApp, Microsoft Teams, Slack
- **Email**: Gmail, Outlook, IMAP
- **Notes**: OneNote
- **Future**: Telegram, SMS, Apple Mail, CRMs, etc.

All connectors follow a unified interface pattern, making it easy to add new platforms without modifying core logic.

## 📁 Architecture

```
app/connectors/
├── __init__.py              # Module exports
├── base.py                   # Core interfaces (ABCs)
├── models.py                 # Unified data models
├── registry.py               # Connector registry (plugin system)
├── middleware.py             # Retry, rate limiting, error handling
├── services.py               # Unified services (aggregation layer)
├── orchestrator.py           # Central coordinator
├── example_usage.py          # Usage examples
├── implementations/          # Concrete connector implementations
│   ├── whatsapp_connector.py
│   ├── teams_connector.py
│   ├── outlook_connector.py
│   ├── gmail_connector.py
│   └── onenote_connector.py
├── tests/                    # Unit tests
│   └── test_whatsapp_connector.py
└── README.md                 # This file
```

## 🏗️ Core Components

### 1. Base Interfaces (`base.py`)

Abstract base classes that define the contract for all connectors:

- **`MessageSourceConnector`**: For messaging platforms (WhatsApp, Teams, etc.)
- **`MailSourceConnector`**: For email platforms (Gmail, Outlook, etc.)
- **`NoteSourceConnector`**: For notes platforms (OneNote, etc.)

### 2. Unified Data Models (`models.py`)

Common data structures that all connectors must map to:

- **`UnifiedMessage`**: Messages from any messaging platform
- **`UnifiedEmail`**: Emails from any email platform
- **`UnifiedNote`**: Notes from any notes platform
- **`UnifiedMeeting`**: Calendar events (for future use)
- **`SourceType`**: Enumeration of all supported platforms

### 3. Connector Registry (`registry.py`)

Plugin mechanism for dynamic registration and retrieval:

```python
from app.connectors.registry import get_registry
from app.connectors.models import SourceType

registry = get_registry()
registry.register_message_connector(SourceType.WHATSAPP, whatsapp_connector)
connector = registry.get_message_connector(SourceType.WHATSAPP)
```

### 4. Unified Services (`services.py`)

Aggregation layer that provides single interface to all connectors:

- **`UnifiedMessageService`**: Access messages from all messaging connectors
- **`UnifiedInboxService`**: Access emails from all mail connectors
- **`UnifiedNotesService`**: Access notes from all notes connectors

### 5. Assistant Orchestrator (`orchestrator.py`)

Central coordinator that:
- Initializes all connectors
- Aggregates data from all sources
- Provides search across all platforms
- Recommends next actions
- Manages local caching

## 🚀 Quick Start

### 1. Initialize Connectors

```python
from app.connectors.registry import get_registry
from app.connectors.models import SourceType
from app.connectors.implementations import (
    WhatsAppConnector,
    GmailConnector,
    OutlookConnector,
)

registry = get_registry()

# Register connectors
whatsapp = WhatsAppConnector()
registry.register_message_connector(SourceType.WHATSAPP, whatsapp)

gmail = GmailConnector()
registry.register_mail_connector(SourceType.GMAIL, gmail)

outlook = OutlookConnector()
registry.register_mail_connector(SourceType.OUTLOOK, outlook)
```

### 2. Use the Orchestrator

```python
from app.connectors.orchestrator import AssistantOrchestrator

orchestrator = AssistantOrchestrator()

# Initialize all connectors
await orchestrator.initialize()

# Get all messages
messages = await orchestrator.get_all_messages(limit=50)

# Get all emails
emails = await orchestrator.get_all_emails(unread_only=True)

# Search across all sources
results = await orchestrator.search_across_sources("meeting")

# Get recommended actions
actions = await orchestrator.get_next_actions()
```

### 3. Use Unified Services Directly

```python
from app.connectors.services import UnifiedMessageService, UnifiedInboxService

message_service = UnifiedMessageService()
inbox_service = UnifiedInboxService()

# Get messages from all connectors
messages = await message_service.get_all_messages(limit=50)

# Send a message
sent_msg = await message_service.send_message(
    content="Hello!",
    to_user_id="+1234567890",
    source_type=SourceType.WHATSAPP,
)

# Get emails
emails = await inbox_service.get_all_emails(unread_only=True)

# Search emails
results = await inbox_service.search_emails("important")
```

## 🔧 Configuration

Connectors are configured via environment variables:

```bash
# WhatsApp
WHATSAPP_API_TOKEN=your_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_id

# Microsoft (Teams, Outlook, OneNote)
MS_CLIENT_ID=your_client_id
MS_CLIENT_SECRET=your_client_secret
MS_TENANT_ID=your_tenant_id

# Gmail (IMAP)
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_IMAP_USERNAME=your_email@gmail.com
EMAIL_IMAP_PASSWORD=your_app_password

# Enable/Disable connectors
ENABLE_WHATSAPP=true
ENABLE_TEAMS=true
ENABLE_OUTLOOK=true
ENABLE_GMAIL=true
ENABLE_ONENOTE=true
```

## 🧪 Testing

Run unit tests:

```bash
pytest app/connectors/tests/
```

Tests use mocks to avoid requiring actual API credentials.

## 📚 Key Design Principles

1. **Interface-Driven**: All connectors implement base interfaces
2. **Dependency Injection**: Services accept connectors via registry
3. **Graceful Degradation**: System continues if one connector fails
4. **Unified Data Models**: All platforms map to common schemas
5. **Plugin Architecture**: Easy to add new connectors
6. **Error Handling**: Retry logic, rate limiting, error boundaries
7. **Async/Await**: Non-blocking operations throughout

## 🔌 Middleware

The `middleware.py` module provides:

- **`@with_retry`**: Automatic retry with exponential backoff
- **`@with_rate_limit`**: Rate limiting for API calls
- **`@with_error_boundary`**: Graceful error handling
- **`@with_logging`**: Automatic logging

Example:

```python
from app.connectors.middleware import with_retry, RetryConfig

@with_retry(RetryConfig(max_retries=3, initial_delay=1.0))
async def fetch_data():
    # Your code here
    pass
```

## 📖 See Also

- [HOW_TO_ADD_NEW_CONNECTOR.md](HOW_TO_ADD_NEW_CONNECTOR.md) - Guide for adding new connectors
- [ARCHITECTURE.md](ARCHITECTURE.md) - Detailed architecture documentation
- [example_usage.py](example_usage.py) - Complete usage examples
