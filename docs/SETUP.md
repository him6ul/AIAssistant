# Setup Instructions

## Quick Start

1. **Install Python 3.11+**
   ```bash
   python3 --version  # Should be 3.11 or higher
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Ollama** (for offline LLM)
   - Download from https://ollama.ai
   - Install and start: `ollama serve`
   - Pull model: `ollama pull llama3`

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

6. **Set up Microsoft Graph API** (for Office 365)
   - Go to https://portal.azure.com
   - Register a new app
   - Get Client ID, Client Secret, Tenant ID
   - Add API permissions: Mail.Read, Notes.Read
   - Add credentials to .env

7. **Get Porcupine Access Key** (for wake word)
   - Sign up at https://console.picovoice.ai
   - Get your access key
   - Add to .env

8. **Run the system**
   ```bash
   ./scripts/run_all.sh
   ```

## Detailed Setup

### OpenAI API Key

1. Go to https://platform.openai.com
2. Create an account or sign in
3. Navigate to API Keys
4. Create a new key
5. Add to .env: `OPENAI_API_KEY=sk-...`

### Microsoft Graph API Setup

1. **Register Azure AD Application**:
   - Go to https://portal.azure.com
   - Azure Active Directory > App registrations > New registration
   - Name: "AI Assistant"
   - Supported account types: Single tenant
   - Redirect URI: `http://localhost:8000/auth/callback`
   - Register

2. **Configure API Permissions**:
   - API permissions > Add a permission
   - Microsoft Graph > Delegated permissions
   - Add: `Mail.Read`, `Notes.Read`, `User.Read`
   - Grant admin consent

3. **Create Client Secret**:
   - Certificates & secrets > New client secret
   - Copy the value (only shown once)
   - Add to .env: `MS_CLIENT_SECRET=...`

4. **Get IDs**:
   - Overview page: Copy Application (client) ID → `MS_CLIENT_ID`
   - Copy Directory (tenant) ID → `MS_TENANT_ID`

### Porcupine Wake Word

1. Sign up at https://console.picovoice.ai
2. Create a new project
3. Get your access key
4. Add to .env: `PORCUPINE_ACCESS_KEY=...`

### Gmail IMAP Setup (Optional)

1. Enable 2-factor authentication
2. Generate app password: https://myaccount.google.com/apppasswords
3. Add to .env:
   ```
   EMAIL_IMAP_SERVER=imap.gmail.com
   EMAIL_IMAP_PORT=993
   EMAIL_IMAP_USERNAME=your_email@gmail.com
   EMAIL_IMAP_PASSWORD=your_app_password
   ```

### Menu Bar App Setup

1. Open `mac-ui/MenuBarApp.xcodeproj` in Xcode
2. Select your development team in Signing & Capabilities
3. Build and run (⌘R)
4. The app will appear in your menu bar

## Troubleshooting

### "Module not found" errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Ollama connection errors
- Check Ollama is running: `ollama list`
- Verify OLLAMA_BASE_URL in .env

### Microsoft Graph authentication errors
- Verify all credentials in .env
- Check API permissions in Azure portal
- Ensure redirect URI matches exactly

### Voice not working
- Check microphone permissions in System Settings
- Verify Porcupine access key
- Check audio device is working

### Menu bar app not connecting
- Ensure backend is running: `curl http://localhost:8000/health`
- Check CORS settings
- Verify network connectivity

## Next Steps

After setup:
1. Test the API: `curl http://localhost:8000/health`
2. Test chat: Use the menu bar app or API
3. Configure ingestion schedules in `config/config.yaml`
4. Set up automatic reminders

