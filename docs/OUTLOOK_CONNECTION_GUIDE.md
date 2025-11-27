# Outlook Connection Guide

This guide explains how to connect the AI Assistant to your Outlook account using Microsoft Graph API.

## 📋 Prerequisites

1. A Microsoft account (Outlook.com, Office 365, or Microsoft 365)
2. Access to Azure Portal (for app registration)
3. Admin permissions (if using organizational account)

## 🔐 Step 1: Register Application in Azure Portal

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Click **New registration**
4. Fill in the details:
   - **Name**: AI Assistant (or your preferred name)
   - **Supported account types**: 
     - For personal: "Accounts in any organizational directory and personal Microsoft accounts"
     - For work: "Accounts in this organizational directory only"
   - **Redirect URI**: Leave blank for now (or use `http://localhost:8000/callback`)
5. Click **Register**
6. **Copy the following values** (you'll need them):
   - **Application (client) ID** → This is your `MS_CLIENT_ID`
   - **Directory (tenant) ID** → This is your `MS_TENANT_ID`

## 🔑 Step 2: Create Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Enter a description (e.g., "AI Assistant Secret")
4. Choose expiration (recommended: 24 months)
5. Click **Add**
6. **IMPORTANT**: Copy the **Value** immediately (you won't see it again!)
   - This is your `MS_CLIENT_SECRET`

## 🔓 Step 3: Configure API Permissions

**IMPORTANT:** For client credentials (app-only) authentication, you MUST use **Application permissions**, not Delegated permissions.

1. In your app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Choose **Application permissions** (NOT Delegated - this is critical!)
5. Add the following permissions:
   - `Mail.Read` - Read user mail (Application permission)
   - `Mail.ReadWrite` - Read and write user mail (Application permission, optional)
   - `User.Read.All` - Read all users' basic profiles (Application permission, needed to list users)
6. Click **Add permissions**
7. **CRITICAL:** Click **Grant admin consent for [your organization]**
   - This button appears at the top of the API permissions page
   - You must be an admin to grant consent
   - If you're not an admin, ask your IT admin to grant consent
   - Wait 5-10 minutes after granting consent for permissions to propagate

## ⚙️ Step 4: Configure .env File

Update your `.env` file with your Outlook credentials:

```bash
# Enable Outlook Connector
ENABLE_OUTLOOK=true

# Microsoft Graph API Configuration
MS_CLIENT_ID=your_application_client_id_here
MS_CLIENT_SECRET=your_client_secret_value_here
MS_TENANT_ID=your_directory_tenant_id_here

# Optional: Redirect URI (for interactive auth)
MS_REDIRECT_URI=http://localhost:8000/callback
```

**Important:**
- Use the **Application (client) ID** for `MS_CLIENT_ID`
- Use the **Client secret Value** (not the Secret ID) for `MS_CLIENT_SECRET`
- Use the **Directory (tenant) ID** for `MS_TENANT_ID`

## 🧪 Step 5: Test the Connection

You can test the connection using Python:

```python
import asyncio
from app.connectors.implementations import OutlookConnector
from app.connectors.registry import get_registry
from app.connectors.models import SourceType

async def test_outlook():
    # Create connector
    outlook = OutlookConnector()
    
    # Try to connect
    connected = await outlook.connect()
    if connected:
        print("✅ Outlook connected successfully!")
        
        # Test fetching emails
        emails = await outlook.fetch_emails(limit=5)
        print(f"📧 Found {len(emails)} emails")
        
        await outlook.disconnect()
    else:
        print("❌ Failed to connect to Outlook")
        print("Check your credentials in .env")

asyncio.run(test_outlook())
```

## 🚀 Step 6: Use with Orchestrator

Once configured, the Outlook connector will be automatically initialized when you use the orchestrator:

```python
from app.connectors.orchestrator import AssistantOrchestrator
from app.connectors.models import SourceType

orchestrator = AssistantOrchestrator()
await orchestrator.initialize()

# Get all emails from Outlook
emails = await orchestrator.get_all_emails(
    source_types=[SourceType.OUTLOOK],
    unread_only=True,
    limit=50
)

# Search emails
results = await orchestrator.search_across_sources("meeting")
outlook_emails = results["emails"]
```

## 🔍 Troubleshooting

### Error: "Outlook credentials not configured"
- Check that `MS_CLIENT_ID`, `MS_CLIENT_SECRET`, and `MS_TENANT_ID` are set in `.env`
- Make sure there are no extra spaces or quotes
- Verify the values are correct (not placeholders)

### Error: "AADSTS7000215: Invalid client secret is provided"
- The client secret has expired or is incorrect
- Generate a new client secret in Azure Portal
- Update `MS_CLIENT_SECRET` in `.env`

### Error: "AADSTS700016: Application not found"
- `MS_CLIENT_ID` is incorrect
- Verify the Application (client) ID in Azure Portal

### Error: "Insufficient privileges to complete the operation"
- API permissions not granted
- Go to Azure Portal → Your App → API permissions
- Click **Grant admin consent** (requires admin rights)
- For personal accounts, consent may be required on first use

### Error: "AADSTS50020: User account not found"
- `MS_TENANT_ID` is incorrect
- Verify the Directory (tenant) ID in Azure Portal
- For personal accounts, use `common` or `consumers` as tenant ID

### Connection works but can't fetch emails
- Check API permissions are granted
- Verify `Mail.Read` permission is added
- Check admin consent is granted

## 📝 Notes

- **Client Secrets expire**: Set a reminder to rotate secrets before expiration
- **Permissions**: Application permissions require admin consent
- **Rate Limits**: Microsoft Graph API has rate limits (check usage in Azure Portal)
- **Tenant ID**: 
  - For personal accounts: Use `common` or your tenant ID
  - For organizational accounts: Use your organization's tenant ID
- **Authentication**: Uses OAuth 2.0 client credentials flow (app-only authentication)

## 🔄 How It Works

### 1. **Server Startup**
   - Checks `ENABLE_OUTLOOK=true` in `.env`
   - Creates `OutlookConnector()` instance
   - Registers it in the connector registry

### 2. **Connection**
   - Uses `MSGraphClient` to authenticate
   - Gets OAuth 2.0 access token using client credentials
   - Verifies connection by getting access token

### 3. **Ready State**
   - Connector is available in orchestrator
   - Can fetch emails via `UnifiedInboxService`
   - Can search across all sources

## 🔒 Security Best Practices

1. **Never commit secrets to git**
   - Keep `.env` in `.gitignore`
   - Use environment variables in production

2. **Rotate secrets regularly**
   - Set expiration reminders
   - Rotate before expiration

3. **Use least privilege**
   - Only grant necessary permissions
   - Review permissions regularly

4. **Monitor usage**
   - Check API usage in Azure Portal
   - Set up alerts for unusual activity

## 📚 Additional Resources

- [Microsoft Graph API Documentation](https://docs.microsoft.com/en-us/graph/overview)
- [Azure Portal](https://portal.azure.com/)
- [Register an application with Microsoft identity platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)

## 💡 Quick Start Checklist

- [ ] Created Azure AD app registration
- [ ] Got Application (client) ID
- [ ] Got Directory (tenant) ID
- [ ] Created client secret and copied value
- [ ] Added API permissions (Mail.Read, Mail.ReadWrite)
- [ ] Granted admin consent (if applicable)
- [ ] Updated `.env` with credentials
- [ ] Set `ENABLE_OUTLOOK=true`
- [ ] Restarted server
- [ ] Tested connection

