# Gmail Connection Guide

This guide explains how to connect the AI Assistant to your Gmail account.

## 📋 Prerequisites

1. A Gmail account
2. 2-Step Verification enabled on your Google account
3. A Gmail App Password (not your regular password)

## 🔐 Step 1: Enable 2-Step Verification

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click **2-Step Verification**
3. Follow the prompts to enable it

## 🔑 Step 2: Generate Gmail App Password

1. Go to [Google Account App Passwords](https://myaccount.google.com/apppasswords)
   - Or: Google Account → Security → 2-Step Verification → App passwords
2. Select **Mail** as the app
3. Select **Other (Custom name)** as the device
4. Enter a name like "AI Assistant"
5. Click **Generate**
6. **Copy the 16-character password** (you'll need this for `.env`)

## ⚙️ Step 3: Configure .env File

Update your `.env` file with your Gmail credentials:

```bash
# Gmail IMAP Configuration
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_IMAP_USERNAME=your_email@gmail.com
EMAIL_IMAP_PASSWORD=your_16_character_app_password
EMAIL_IMAP_USE_SSL=true

# Enable Gmail Connector
ENABLE_GMAIL=true
```

**Important:**
- Use your **full Gmail address** for `EMAIL_IMAP_USERNAME`
- Use the **16-character App Password** (not your regular password)
- The App Password has no spaces - it's 16 characters like: `abcd efgh ijkl mnop`

## 🧪 Step 4: Test the Connection

You can test the connection using Python:

```python
import asyncio
from app.connectors.implementations import GmailConnector
from app.connectors.registry import get_registry
from app.connectors.models import SourceType

async def test_gmail():
    # Create connector
    gmail = GmailConnector()
    
    # Try to connect
    connected = await gmail.connect()
    if connected:
        print("✅ Gmail connected successfully!")
        
        # Test fetching emails
        emails = await gmail.fetch_emails(limit=5)
        print(f"📧 Found {len(emails)} emails")
        
        await gmail.disconnect()
    else:
        print("❌ Failed to connect to Gmail")
        print("Check your credentials in .env")

asyncio.run(test_gmail())
```

## 🚀 Step 5: Use with Orchestrator

Once configured, the Gmail connector will be automatically initialized when you use the orchestrator:

```python
from app.connectors.orchestrator import AssistantOrchestrator
from app.connectors.models import SourceType

orchestrator = AssistantOrchestrator()
await orchestrator.initialize()

# Get all emails from Gmail
emails = await orchestrator.get_all_emails(
    source_types=[SourceType.GMAIL],
    unread_only=True,
    limit=50
)

# Search emails
results = await orchestrator.search_across_sources("meeting")
gmail_emails = results["emails"]
```

## 🔍 Troubleshooting

### Error: "Gmail credentials not configured"
- Check that `EMAIL_IMAP_USERNAME` and `EMAIL_IMAP_PASSWORD` are set in `.env`
- Make sure there are no extra spaces or quotes

### Error: "Authentication failed"
- Verify you're using an **App Password**, not your regular password
- Make sure 2-Step Verification is enabled
- Regenerate the App Password if needed

### Error: "Connection refused" or "Timeout"
- Check your internet connection
- Verify `EMAIL_IMAP_SERVER=imap.gmail.com` and `EMAIL_IMAP_PORT=993`
- Check if your firewall is blocking IMAP connections

### Error: "Less secure app access"
- This error shouldn't occur with App Passwords
- If you see it, make sure you're using an App Password, not your regular password

## 📝 Notes

- **App Passwords are required** - Gmail no longer allows "less secure apps" to use regular passwords
- The connector uses **IMAP** which is read-only for sending (you'd need SMTP for sending)
- Emails are fetched and converted to `UnifiedEmail` format
- The connector supports searching, fetching by folder, and filtering unread emails

## 🔄 Next Steps

After connecting Gmail:
1. The connector will be available in the orchestrator
2. You can fetch emails: `orchestrator.get_all_emails()`
3. You can search emails: `orchestrator.search_across_sources()`
4. You can get action recommendations: `orchestrator.get_next_actions()`

