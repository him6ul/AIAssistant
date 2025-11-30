# Google Calendar Setup Guide

## Overview

The Google Calendar connector allows you to check your meetings and events by asking:
- "Jarvis, do I have any meetings today?"
- "Jarvis, do I have any meetings today in Google Calendar?"
- "Jarvis, what meetings do I have?"

## Setup Steps

### 1. Install Dependencies

The required packages are already in `requirements.txt`. Install them:

```bash
pip install -r requirements.txt
```

### 2. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Calendar API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

### 3. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" (unless you have a Google Workspace)
   - Fill in required fields (App name, User support email, etc.)
   - Add your email to test users
   - Save and continue
4. For Application type, choose "Desktop app"
5. Name it (e.g., "AI Assistant Calendar")
6. Click "Create"
7. Download the JSON file

### 4. Save Credentials File

1. Save the downloaded JSON file as:
   ```
   config/google_calendar_credentials.json
   ```

2. Or set the path in your `.env` file:
   ```bash
   GOOGLE_CALENDAR_CREDENTIALS_FILE=config/google_calendar_credentials.json
   ```

### 5. First-Time Authentication

When you first run the assistant and ask about meetings, it will:
1. Open a browser window for Google OAuth authentication
2. Ask you to sign in and grant calendar access
3. Save the token to `config/google_calendar_token.pickle` (or path specified in `.env`)

**Note:** The token file will be created automatically after first authentication.

### 6. Environment Variables (Optional)

You can customize paths in your `.env` file:

```bash
# Google Calendar credentials file path
GOOGLE_CALENDAR_CREDENTIALS_FILE=config/google_calendar_credentials.json

# Google Calendar token file path (stores authenticated token)
GOOGLE_CALENDAR_TOKEN_FILE=config/google_calendar_token.pickle
```

## Usage

Once set up, you can ask:

- "Jarvis, do I have any meetings today?"
- "Jarvis, what meetings do I have?"
- "Jarvis, do I have any meetings today in Google Calendar?"

The assistant will:
1. Connect to your Google Calendar
2. Fetch remaining meetings for today
3. Tell you how many meetings you have and their details (time, title, location)

## Features

- **Remaining Meetings**: Only shows meetings that haven't ended yet
- **Today's View**: Shows all remaining meetings for the current day
- **Formatted Output**: Displays meeting title, time, and location in a readable format

## Troubleshooting

### "I can't check your calendar right now"
- Check that `google_calendar_credentials.json` exists in the config folder
- Verify the file is valid JSON

### "I couldn't connect to your Google Calendar"
- Make sure Google Calendar API is enabled in your Google Cloud project
- Check that OAuth consent screen is configured
- Try deleting `google_calendar_token.pickle` and re-authenticating

### Token Expired
- Delete the token file and re-authenticate
- The token should auto-refresh, but if it fails, delete and re-authenticate

## Security Notes

- Keep `google_calendar_credentials.json` and `google_calendar_token.pickle` secure
- Don't commit these files to version control
- Add them to `.gitignore`:
  ```
  config/google_calendar_credentials.json
  config/google_calendar_token.pickle
  ```

