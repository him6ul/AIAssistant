# Architecture Overview

## Command Handler System

The assistant now has a command handler system that processes basic commands before routing to the LLM. This provides faster, more reliable responses for common queries.

### Supported Commands

- **Weather**: "What is the weather?", "What's the temperature in New York?"
- **Time**: "What time is it?", "What's the current time?"
- **Date**: "What date is it?", "What's today's date?"

### How It Works

1. User sends a message via `/chat` endpoint
2. Command handler checks if the message matches a known command pattern
3. If matched, the command handler processes it directly (no LLM call)
4. If not matched, the message is routed to the LLM for processing

### Adding New Commands

1. Create a handler class in `app/commands/handlers.py`:
```python
class YourCommandHandler:
    def can_handle(self, text: str) -> bool:
        # Check if this handler can process the command
        return "your_keyword" in text.lower()
    
    async def handle(self, text: str) -> CommandResponse:
        # Process the command and return response
        return CommandResponse(
            handled=True,
            response="Your response",
            command_type=CommandType.YOUR_TYPE
        )
```

2. Register it in `app/commands/handler.py`:
```python
self.handlers = [
    WeatherHandler(),
    TimeHandler(),
    DateHandler(),
    YourCommandHandler(),  # Add here
]
```

## Connector Architecture

The connector system provides a plugin-based architecture for integrating with various communication and productivity services.

### Architecture Components

1. **Base Connector** (`app/connectors/base.py`): Abstract interface all connectors implement
2. **Connector Registry** (`app/connectors/registry.py`): Manages connector registration and initialization
3. **Connector Loader** (`app/connectors/loader.py`): Loads connectors at startup
4. **Individual Connectors**: Service-specific implementations

### Available Connectors

- **Outlook** (`outlook_connector.py`): Microsoft Outlook via Graph API
- **Gmail** (`gmail_connector.py`): Gmail via IMAP

### Adding New Connectors

See `app/connectors/README.md` for detailed instructions.

### Using Connectors

```python
from app.connectors.registry import get_connector_registry

registry = get_connector_registry()
outlook = registry.get("outlook")
if outlook and await outlook.is_available():
    messages = await outlook.get_messages(limit=10, unread_only=True)
```

## Request Flow

```
User Input
    ↓
Chat Endpoint (/chat)
    ↓
Command Handler (checks for basic commands)
    ├─→ Handled? → Return response
    └─→ Not handled? → LLM Router
                        ├─→ Online? → OpenAI
                        └─→ Offline? → Ollama
```

## Benefits

1. **Faster Responses**: Basic commands don't require LLM calls
2. **Lower Costs**: Reduces API calls for simple queries
3. **Extensibility**: Easy to add new commands and connectors
4. **Modularity**: Clear separation of concerns
5. **Maintainability**: Each component is independent and testable

## Configuration

### Weather API

Add to `.env`:
```
OPENWEATHER_API_KEY=your_api_key_here
DEFAULT_LOCATION=San Francisco  # Optional default location
```

Get API key from: https://openweathermap.org/api

### Connectors

Connectors are automatically initialized based on environment variables:
- Outlook: `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, `MS_TENANT_ID`
- Gmail: `EMAIL_IMAP_USERNAME`, `EMAIL_IMAP_PASSWORD`, `EMAIL_IMAP_SERVER`

