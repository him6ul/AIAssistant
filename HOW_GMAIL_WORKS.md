# How Gmail Connector Works

## 📋 Overview

When you set `ENABLE_GMAIL=true` in your `.env` file, the Gmail connector will be automatically registered and initialized when the server starts.

## 🔄 How It Works

### 1. **Server Startup** (`app/main.py`)
   - Calls `load_connectors()` which checks `ENABLE_GMAIL`
   - If `ENABLE_GMAIL=true`, registers the Gmail connector
   - Calls `initialize_connectors()` which connects to Gmail

### 2. **Connector Registration** (`app/connectors/loader.py`)
   ```python
   if enable_gmail:
       gmail = GmailConnector()
       registry.register_mail_connector(SourceType.GMAIL, gmail)
   ```

### 3. **Connection** (`app/connectors/implementations/gmail_connector.py`)
   - Reads credentials from `.env`:
     - `EMAIL_IMAP_SERVER` (default: `imap.gmail.com`)
     - `EMAIL_IMAP_PORT` (default: `993`)
     - `EMAIL_IMAP_USERNAME` (your Gmail address)
     - `EMAIL_IMAP_PASSWORD` (Gmail App Password)
   - Connects via IMAP SSL
   - Verifies credentials

### 4. **Usage**
   Once connected, you can use the orchestrator to:
   - Fetch emails: `orchestrator.get_all_emails()`
   - Search emails: `orchestrator.search_across_sources()`
   - Get unread emails: `orchestrator.get_all_emails(unread_only=True)`

## ✅ Required Configuration

In your `.env` file, you need:

```bash
# Enable Gmail connector
ENABLE_GMAIL=true

# Gmail IMAP credentials
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_IMAP_USERNAME=your_email@gmail.com
EMAIL_IMAP_PASSWORD=your_16_char_app_password
EMAIL_IMAP_USE_SSL=true
```

## 🔐 Getting Gmail App Password

1. Go to [Google Account App Passwords](https://myaccount.google.com/apppasswords)
2. Enable 2-Step Verification if not already enabled
3. Generate App Password for "Mail"
4. Copy the 16-character password
5. Add it to `.env` as `EMAIL_IMAP_PASSWORD`

## 🧪 Testing Connection

Run the test script:
```bash
python3 test_gmail_connection.py
```

This will:
- Check if Gmail is enabled
- Verify credentials are set
- Test connection to Gmail
- Fetch sample emails
- List folders

## 📊 What Happens on Server Start

1. **Load Phase**: 
   - Checks `ENABLE_GMAIL` environment variable
   - If `true`, creates `GmailConnector()` instance
   - Registers it in the connector registry

2. **Initialize Phase**:
   - Calls `gmail.connect()` 
   - Connects to `imap.gmail.com:993` using SSL
   - Logs in with `EMAIL_IMAP_USERNAME` and `EMAIL_IMAP_PASSWORD`
   - Sets `_connected = True` on success

3. **Ready State**:
   - Connector is available in orchestrator
   - Can fetch emails via `UnifiedInboxService`
   - Can search across all sources

## 🔍 Logs to Watch

When the server starts, you should see:
```
INFO | Registered Gmail connector
INFO | Connected gmail connector
INFO | Initialized 1 connector(s)
```

If there's an error:
```
ERROR | Failed to initialize Gmail connector: [error message]
WARNING | Gmail credentials not configured
```

## 🚀 Using Gmail in Your Code

```python
from app.connectors.orchestrator import AssistantOrchestrator
from app.connectors.models import SourceType

# Initialize orchestrator (connectors auto-connect)
orchestrator = AssistantOrchestrator()
await orchestrator.initialize()

# Get emails from Gmail
emails = await orchestrator.get_all_emails(
    source_types=[SourceType.GMAIL],
    unread_only=True,
    limit=50
)

# Search across all sources (including Gmail)
results = await orchestrator.search_across_sources("meeting")
gmail_emails = results["emails"]
```

## ⚠️ Troubleshooting

### "Gmail credentials not configured"
- Check that `EMAIL_IMAP_USERNAME` and `EMAIL_IMAP_PASSWORD` are set
- Make sure there are no extra spaces or quotes

### "Authentication failed"
- Verify you're using an **App Password**, not your regular password
- Make sure 2-Step Verification is enabled
- Regenerate the App Password if needed

### "Connection refused"
- Check your internet connection
- Verify firewall isn't blocking IMAP (port 993)
- Check that `EMAIL_IMAP_SERVER=imap.gmail.com`

### Connector not initializing
- Check logs for error messages
- Verify `ENABLE_GMAIL=true` (not `True` or `TRUE`)
- Make sure credentials are in `.env` file

