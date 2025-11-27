# How to Add a New Connector

This guide explains how to add a new connector to the system without modifying any core logic.

## 📋 Prerequisites

- Understand the base interfaces (`base.py`)
- Know the API/SDK for your target platform
- Have API credentials ready

## 🎯 Step-by-Step Guide

### Step 1: Choose the Right Interface

Determine which base interface your connector should implement:

- **`MessageSourceConnector`**: For messaging platforms (Slack, Telegram, SMS)
- **`MailSourceConnector`**: For email platforms (Gmail, Outlook, IMAP, Apple Mail)
- **`NoteSourceConnector`**: For notes platforms (Evernote, etc.)

### Step 2: Add Source Type (if new platform)

If your platform doesn't exist in the `SourceType` enum, add it:

**File**: `app/connectors/models.py`

```python
class SourceType(str, Enum):
    # ... existing types ...
    YOUR_NEW_PLATFORM = "your_new_platform"  # Add here
```

### Step 3: Create Connector Implementation

Create a new file in `app/connectors/implementations/`:

**File**: `app/connectors/implementations/your_platform_connector.py`

```python
"""
Your Platform connector implementation.
"""

from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
from app.connectors.base import MessageSourceConnector, ConnectorCapabilities
from app.connectors.models import UnifiedMessage, SourceType
from app.connectors.middleware import with_retry, RetryConfig, with_error_boundary, with_logging
from app.utils.logger import get_logger

logger = get_logger(__name__)


class YourPlatformConnector(MessageSourceConnector):
    """
    Your Platform connector.
    
    Implements MessageSourceConnector interface.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize connector."""
        self.api_key = api_key or os.getenv("YOUR_PLATFORM_API_KEY")
        self._connected = False
        self._client = None
        self._event_callbacks = []
    
    @property
    def source_type(self) -> SourceType:
        """Return source type."""
        return SourceType.YOUR_NEW_PLATFORM
    
    @with_logging()
    @with_retry(RetryConfig(max_retries=3))
    async def connect(self) -> bool:
        """Connect to platform API."""
        try:
            # Initialize API client
            # Test connection
            self._connected = True
            logger.info("Your Platform connector connected")
            return True
        except Exception as e:
            logger.error(f"Error connecting: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from platform."""
        self._connected = False
        logger.info("Your Platform connector disconnected")
    
    @with_error_boundary("Failed to fetch messages", return_on_error=[])
    @with_logging()
    async def fetch_messages(
        self,
        limit: int = 50,
        since: Optional[datetime] = None,
        thread_id: Optional[str] = None,
    ) -> List[UnifiedMessage]:
        """Fetch messages from platform."""
        # 1. Call platform API
        # 2. Convert platform-specific format to UnifiedMessage
        # 3. Return list of UnifiedMessage objects
        
        messages = []
        # ... your implementation ...
        return messages
    
    @with_error_boundary("Failed to send message")
    @with_logging()
    async def send_message(
        self,
        content: str,
        to_user_id: str,
        thread_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> UnifiedMessage:
        """Send message via platform."""
        # 1. Call platform API to send
        # 2. Convert response to UnifiedMessage
        # 3. Return UnifiedMessage
        
        # ... your implementation ...
        return UnifiedMessage(...)
    
    async def subscribe_to_events(
        self,
        callback: Callable[[UnifiedMessage], None],
    ) -> None:
        """Subscribe to real-time events."""
        self._event_callbacks.append(callback)
        # Set up webhooks/polling if needed
    
    def get_capabilities(self) -> ConnectorCapabilities:
        """Return connector capabilities."""
        return ConnectorCapabilities(
            can_send=True,
            can_receive=True,
            can_search=True,
            # ... set based on platform capabilities
        )
    
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected
```

### Step 4: Convert Platform Data to Unified Models

**Key**: Convert platform-specific data to unified models:

```python
def _convert_platform_message(self, platform_msg: Dict[str, Any]) -> UnifiedMessage:
    """Convert platform message to UnifiedMessage."""
    return UnifiedMessage(
        id=f"{self.source_type.value}_{platform_msg['id']}",
        source_type=self.source_type,
        source_id=platform_msg['id'],
        content=platform_msg['text'],
        from_user={
            "id": platform_msg['from']['id'],
            "name": platform_msg['from']['name'],
        },
        timestamp=datetime.fromisoformat(platform_msg['timestamp']),
        raw_data=platform_msg,  # Preserve original data
    )
```

### Step 5: Export in `__init__.py`

**File**: `app/connectors/implementations/__init__.py`

```python
from app.connectors.implementations.your_platform_connector import YourPlatformConnector

__all__ = [
    # ... existing connectors ...
    "YourPlatformConnector",
]
```

### Step 6: Register Connector

In your application initialization code:

```python
from app.connectors.registry import get_registry
from app.connectors.models import SourceType
from app.connectors.implementations import YourPlatformConnector

registry = get_registry()
connector = YourPlatformConnector()
registry.register_message_connector(SourceType.YOUR_NEW_PLATFORM, connector)
```

### Step 7: Add Configuration (Optional)

Add environment variables to `.env.sample`:

```bash
# Your Platform
YOUR_PLATFORM_API_KEY=your_api_key
ENABLE_YOUR_PLATFORM=true
```

## ✅ Checklist

- [ ] Added `SourceType` enum value (if new platform)
- [ ] Created connector class implementing base interface
- [ ] Implemented all required methods
- [ ] Added data conversion to unified models
- [ ] Added error handling and retry logic
- [ ] Added logging
- [ ] Exported in `__init__.py`
- [ ] Registered in application initialization
- [ ] Added configuration variables
- [ ] Tested connector

## 🧪 Testing

Create unit tests in `app/connectors/tests/`:

```python
# app/connectors/tests/test_your_platform_connector.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.connectors.implementations.your_platform_connector import YourPlatformConnector

@pytest.mark.asyncio
async def test_connect():
    connector = YourPlatformConnector()
    # Test connection logic
    pass
```

## 🎉 Done!

Your connector is now integrated. The orchestrator will automatically:
- Initialize it
- Include it in aggregated queries
- Include it in search results
- Include it in action recommendations

**No other code needs to be modified!**

## 📝 Example: Adding Telegram Connector

See `app/connectors/implementations/gmail_connector.py` or `app/connectors/implementations/outlook_connector.py` as reference implementations.

Key points:
1. Implement `MessageSourceConnector`
2. Use middleware decorators for retry/error handling
3. Convert Telegram messages to `UnifiedMessage`
4. Register in registry
5. Done!

## 🆘 Troubleshooting

**Q: My connector isn't being initialized**
- Check that it's registered in the registry
- Verify `connect()` returns `True`
- Check logs for errors

**Q: Data conversion is failing**
- Ensure all required fields are mapped
- Check `raw_data` field preserves original data
- Verify datetime formats

**Q: API calls are failing**
- Check API credentials
- Verify retry logic is working
- Check rate limiting

## 📚 See Also

- [base.py](base.py) - Interface definitions
- [models.py](models.py) - Unified data models
- [registry.py](registry.py) - Registration mechanism
- [example_usage.py](example_usage.py) - Usage examples

