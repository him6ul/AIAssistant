# Connector Architecture Documentation

## 🏛️ Architecture Overview

The connector architecture follows a **layered, plugin-based design** that enables easy extension without modifying core logic.

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│              (AssistantOrchestrator)                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Unified Services Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Message    │  │    Inbox     │  │    Notes     │     │
│  │   Service    │  │   Service    │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Registry Layer                            │
│              (ConnectorRegistry)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Message  │  │   Mail   │  │   Note   │                 │
│  │Connectors│  │Connectors│  │Connectors│                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Interface Layer (ABCs)                      │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │MessageSource      │  │MailSource        │               │
│  │Connector          │  │Connector         │               │
│  └──────────────────┘  └──────────────────┘               │
│  ┌──────────────────┐                                      │
│  │NoteSource         │                                      │
│  │Connector          │                                      │
│  └──────────────────┘                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Implementation Layer                            │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐           │
│  │Whats │ │Teams │ │Outlook│ │Gmail │ │OneNote│           │
│  │ App  │ │      │ │       │ │      │ │       │           │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                  Platform APIs                                │
│  WhatsApp API │ Graph API │ Gmail API │ IMAP │ etc.        │
└──────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

### 1. Initialization Flow

```
Application Start
    │
    ├─> Create ConnectorRegistry
    │
    ├─> Initialize Connectors (WhatsApp, Teams, etc.)
    │   │
    │   └─> Register in Registry
    │
    ├─> Create AssistantOrchestrator
    │   │
    │   ├─> Create Unified Services
    │   │   ├─> UnifiedMessageService
    │   │   ├─> UnifiedInboxService
    │   │   └─> UnifiedNotesService
    │   │
    │   └─> Initialize All Connectors
    │       └─> Connect to Platform APIs
    │
    └─> Ready to Use
```

### 2. Data Fetching Flow

```
User Request: "Get all messages"
    │
    ├─> AssistantOrchestrator.get_all_messages()
    │
    ├─> UnifiedMessageService.get_all_messages()
    │
    ├─> Registry.get_all_message_connectors()
    │   │
    │   ├─> WhatsAppConnector.fetch_messages()
    │   │   └─> Convert to UnifiedMessage
    │   │
    │   ├─> TeamsConnector.fetch_messages()
    │   │   └─> Convert to UnifiedMessage
    │   │
    │   └─> ... (other connectors)
    │
    ├─> Aggregate Results
    │
    ├─> Sort by Timestamp
    │
    └─> Return Unified List
```

### 3. Data Conversion Flow

```
Platform-Specific Data
    │
    ├─> Connector.fetch_*()
    │   │
    │   └─> Platform API Response
    │       (e.g., WhatsApp JSON, Teams Graph API, Gmail IMAP)
    │
    ├─> _convert_*() Method
    │   │
    │   └─> Unified Model
    │       (UnifiedMessage, UnifiedEmail, UnifiedNote)
    │
    └─> Return to Service Layer
```

## 🧩 Component Details

### 1. Base Interfaces (`base.py`)

**Purpose**: Define contracts that all connectors must implement.

**Key Interfaces**:
- `MessageSourceConnector`: For messaging platforms
- `MailSourceConnector`: For email platforms
- `NoteSourceConnector`: For notes platforms

**Design Pattern**: Abstract Base Classes (ABCs) with `@abstractmethod` decorators.

### 2. Unified Models (`models.py`)

**Purpose**: Common data structures that all platforms map to.

**Key Models**:
- `UnifiedMessage`: Messages from any messaging platform
- `UnifiedEmail`: Emails from any email platform
- `UnifiedNote`: Notes from any notes platform

**Design Pattern**: Dataclasses with `to_dict()` serialization.

### 3. Connector Registry (`registry.py`)

**Purpose**: Plugin mechanism for dynamic connector management.

**Features**:
- Singleton pattern
- Type-safe registration/retrieval
- Support for multiple connector types

**Design Pattern**: Registry/Plugin pattern.

### 4. Unified Services (`services.py`)

**Purpose**: Aggregation layer that provides single interface to all connectors.

**Services**:
- `UnifiedMessageService`: Aggregates messages
- `UnifiedInboxService`: Aggregates emails
- `UnifiedNotesService`: Aggregates notes

**Design Pattern**: Service layer pattern with dependency injection.

### 5. Assistant Orchestrator (`orchestrator.py`)

**Purpose**: Central coordinator for all operations.

**Responsibilities**:
- Initialize/shutdown connectors
- Aggregate data from all sources
- Provide search across platforms
- Recommend actions
- Manage local caching

**Design Pattern**: Orchestrator/Facade pattern.

### 6. Middleware (`middleware.py`)

**Purpose**: Cross-cutting concerns (retry, rate limiting, error handling).

**Decorators**:
- `@with_retry`: Automatic retry with exponential backoff
- `@with_rate_limit`: Rate limiting
- `@with_error_boundary`: Graceful error handling
- `@with_logging`: Automatic logging

**Design Pattern**: Decorator pattern.

## 🔐 Design Principles

### 1. SOLID Principles

- **Single Responsibility**: Each connector handles one platform
- **Open/Closed**: Open for extension (new connectors), closed for modification
- **Liskov Substitution**: All connectors are substitutable via interfaces
- **Interface Segregation**: Separate interfaces for messages, mail, notes
- **Dependency Inversion**: Depend on abstractions (interfaces), not concretions

### 2. Dependency Injection

All services accept connectors via registry, not direct instantiation:

```python
# ✅ Good: Dependency injection
orchestrator = AssistantOrchestrator(registry=registry)

# ❌ Bad: Direct dependency
orchestrator = AssistantOrchestrator()
orchestrator.whatsapp = WhatsAppConnector()  # Tight coupling
```

### 3. Graceful Degradation

System continues operating even if some connectors fail:

```python
try:
    messages = await connector.fetch_messages()
except Exception as e:
    logger.error(f"Connector failed: {e}")
    messages = []  # Return empty list, continue with other connectors
```

### 4. Error Boundaries

Errors in one connector don't break the entire system:

```python
@with_error_boundary("Failed to fetch messages", return_on_error=[])
async def fetch_messages():
    # If this fails, returns [] instead of crashing
    pass
```

## 🔄 Sequence Diagrams

### Fetching Messages

```
User → Orchestrator → MessageService → Registry
                                    ↓
                              Get Connectors
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
              WhatsApp          Teams          Slack
                    │               │               │
                    └───────────────┼───────────────┘
                                    ↓
                              Convert to UnifiedMessage
                                    ↓
                              Aggregate & Sort
                                    ↓
                              Return to User
```

### Adding New Connector

```
Developer → Create Connector Class
         → Implement Interface
         → Register in Registry
         → (No other code changes needed)
         ↓
    Orchestrator automatically includes it
         ↓
    Available in all queries
```

## 📊 Data Model Relationships

```
UnifiedMessage
    ├─> source_type: SourceType (WHATSAPP, TEAMS, etc.)
    ├─> content: str
    ├─> from_user: Dict
    ├─> to_users: List[Dict]
    └─> raw_data: Dict (platform-specific, preserved)

UnifiedEmail
    ├─> source_type: SourceType (GMAIL, OUTLOOK, etc.)
    ├─> subject: str
    ├─> body_text: str
    ├─> from_address: Dict
    ├─> to_addresses: List[Dict]
    └─> raw_data: Dict (platform-specific, preserved)

UnifiedNote
    ├─> source_type: SourceType (ONENOTE, etc.)
    ├─> title: str
    ├─> content: str
    ├─> notebook_id: Optional[str]
    └─> raw_data: Dict (platform-specific, preserved)
```

## 🚀 Extension Points

### Adding New Connector Type

1. Create new base interface (if needed)
2. Add to registry methods
3. Create unified service (if needed)
4. Update orchestrator

### Adding New Platform

1. Implement existing interface
2. Register in registry
3. Done! (No other changes needed)

### Adding New Capability

1. Add to `ConnectorCapabilities`
2. Update interface methods (if needed)
3. Implement in connectors
4. Use in services/orchestrator

## 🔍 Testing Strategy

### Unit Tests

- Test each connector in isolation
- Use mocks for API calls
- Test data conversion
- Test error handling

### Integration Tests

- Test registry registration
- Test service aggregation
- Test orchestrator coordination

### End-to-End Tests

- Test full flow: fetch → convert → aggregate → return
- Test with multiple connectors
- Test error scenarios

## 📈 Performance Considerations

1. **Caching**: Orchestrator caches fetched data
2. **Parallel Fetching**: Services fetch from all connectors concurrently
3. **Rate Limiting**: Middleware prevents API abuse
4. **Lazy Loading**: Connectors only connect when needed
5. **Pagination**: Limit results to prevent memory issues

## 🔒 Security Considerations

1. **Credentials**: Stored in environment variables, never in code
2. **Token Management**: Connectors handle token refresh
3. **Error Messages**: Don't expose sensitive data in logs
4. **Input Validation**: Validate all inputs before API calls
5. **HTTPS Only**: All API calls use HTTPS

## 📚 References

- [README.md](README.md) - Quick start guide
- [HOW_TO_ADD_NEW_CONNECTOR.md](HOW_TO_ADD_NEW_CONNECTOR.md) - Extension guide
- [example_usage.py](example_usage.py) - Code examples

