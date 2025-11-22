# Connector Architecture

This directory contains the plugin-based connector architecture for integrating with various communication and productivity services.

## Architecture Overview

The connector system uses a plugin-based architecture that makes it easy to add new service integrations:

1. **Base Connector** (`base.py`): Abstract base class that all connectors must implement
2. **Connector Registry** (`registry.py`): Manages registration and initialization of connectors
3. **Connector Loader** (`loader.py`): Loads and initializes connectors at startup
4. **Individual Connectors**: Implementation for each service (Outlook, Gmail, etc.)

## Adding a New Connector

To add a new connector (e.g., Yahoo Mail, Teams, Slack):

### Step 1: Create the Connector Class

Create a new file `app/connectors/your_service_connector.py`:

```python
from app.connectors.base import BaseConnector, ConnectorType, Message
from typing import List, Optional
from datetime import datetime

class YourServiceConnector(BaseConnector):
    """Your service connector."""
    
    def __init__(self, name: str = "your_service", **kwargs):
        super().__init__(name, ConnectorType.EMAIL)  # or appropriate type
        # Initialize your service-specific attributes
    
    async def initialize(self) -> bool:
        """Initialize and authenticate with your service."""
        try:
            # Your initialization logic
            self.initialized = True
            return True
        except Exception as e:
            return False
    
    async def is_available(self) -> bool:
        """Check if connector is available."""
        return self.initialized
    
    async def get_messages(
        self,
        limit: int = 50,
        unread_only: bool = False,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """Get messages from your service."""
        # Your implementation
        return []
    
    async def send_message(
        self,
        to: str,
        subject: Optional[str],
        body: str,
        **kwargs
    ) -> bool:
        """Send message via your service."""
        # Your implementation
        return True
```

### Step 2: Register the Connector

Add to `app/connectors/loader.py`:

```python
from app.connectors.your_service_connector import YourServiceConnector

def load_connectors():
    registry = get_connector_registry()
    registry.register("your_service", YourServiceConnector)
    # ... existing registrations
```

### Step 3: Configure Initialization

Update `initialize_connectors()` in `loader.py` to initialize your connector based on configuration:

```python
async def initialize_connectors():
    # ... existing code
    if os.getenv("YOUR_SERVICE_API_KEY"):
        connectors_to_init.append("your_service")
```

## Available Connectors

- **Outlook** (`outlook_connector.py`): Microsoft Outlook via Graph API
- **Gmail** (`gmail_connector.py`): Gmail via IMAP

## Using Connectors

```python
from app.connectors.registry import get_connector_registry

registry = get_connector_registry()

# Get a specific connector
outlook = registry.get("outlook")
if outlook:
    messages = await outlook.get_messages(limit=10, unread_only=True)

# Get all email connectors
email_connectors = registry.get_all(ConnectorType.EMAIL)
for connector in email_connectors:
    if await connector.is_available():
        messages = await connector.get_messages()
```

## Connector Types

- `EMAIL`: Email services (Outlook, Gmail, Yahoo, etc.)
- `CALENDAR`: Calendar services
- `NOTES`: Note-taking services (OneNote, Evernote, etc.)
- `MESSAGING`: Messaging services (Teams, Slack, etc.)
- `TASKS`: Task management services

## Best Practices

1. **Error Handling**: Always handle errors gracefully and log them
2. **Authentication**: Store credentials securely (use environment variables)
3. **Rate Limiting**: Respect API rate limits
4. **Async Operations**: All connector methods should be async
5. **Initialization**: Check availability before using connectors
6. **Message Format**: Use the standard `Message` model for consistency

