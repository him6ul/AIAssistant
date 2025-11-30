# Google Calendar Credentials Setup

## Quick Setup Guide

### Step 1: Create Google Cloud Project
1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable "Google Calendar API" in APIs & Services > Library

### Step 2: Create OAuth 2.0 Credentials
1. Go to APIs & Services > Credentials
2. Click "Create Credentials" > "OAuth client ID"
3. Configure OAuth consent screen (if first time):
   - Choose "External"
   - Fill required fields
   - Add your email as test user
4. For Application type: Choose "Desktop app"
5. Name it (e.g., "AI Assistant Calendar")
6. Click "Create"
7. **Download the JSON file**

### Step 3: Save Credentials
1. Save the downloaded JSON file as:
   ```
   config/google_calendar_credentials.json
   ```

### Step 4: First Authentication
When you first ask about meetings, the assistant will:
- Open a browser for Google OAuth
- Ask you to sign in and grant calendar access
- Save the token automatically

## File Structure
```
config/
  ├── google_calendar_credentials.json  ← Download from Google Cloud Console
  └── google_calendar_token.pickle      ← Auto-created after first auth
```

## Troubleshooting

**"Credentials file not found"**
- Make sure the JSON file is saved as `config/google_calendar_credentials.json`
- Check file permissions (should be readable)

**"I couldn't connect to your Google Calendar"**
- Verify Google Calendar API is enabled in Google Cloud Console
- Check that OAuth consent screen is configured
- Try deleting `google_calendar_token.pickle` and re-authenticating

## Security Note
- Never commit these files to git
- They're already in `.gitignore`

