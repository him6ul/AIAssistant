# AI Personal Assistant for macOS

A complete Mac-local AI Personal Assistant with hybrid LLM support (OpenAI + Ollama), voice activation, email/OneNote ingestion, task extraction, and macOS integration.

## Features

- **Hybrid LLM Mode**: Automatically switches between OpenAI GPT-4/GPT-5 (online) and Ollama models (offline)
- **Voice First**: Wake word detection with Porcupine, local Whisper STT, and TTS
- **Data Ingestion**: 
  - OneNote via Microsoft Graph API
  - Email via Office 365 Graph API and IMAP
- **Task Extraction**: LLM-powered task extraction from emails and notes
- **Action Execution**: Create reminders, calendar events, and email drafts via AppleScript
- **Mac Menu Bar App**: SwiftUI menu bar application with chat and task management
- **Background Workers**: Automated ingestion and reminder scheduling

## Architecture

```
AI_Assistant/
├── app/                    # Python backend
│   ├── main.py            # Main entry point
│   ├── llm_router.py      # Hybrid LLM router
│   ├── network.py         # Network detection
│   ├── stt.py             # Speech-to-text
│   ├── tts.py             # Text-to-speech
│   ├── voice_listener.py  # Voice activation
│   ├── scheduler/         # Background workers
│   │   ├── email_scheduler.py
│   │   ├── onenote_scheduler.py
│   │   └── reminder_scheduler.py
│   ├── ingestion/         # Data ingestion
│   │   ├── ms_graph_client.py
│   │   ├── onenote_ingestor.py
│   │   ├── email_o365_ingestor.py
│   │   ├── email_imap_ingestor.py
│   │   └── github_client.py
│   ├── tasks/             # Task management
│   │   ├── extractor.py
│   │   ├── storage.py
│   │   └── models.py
│   ├── actions/           # Action execution
│   │   ├── executor.py
│   │   └── capabilities.py
│   ├── api/               # FastAPI server
│   │   └── server.py
│   └── utils/             # Utilities
│       └── logger.py
├── mac-ui/                # SwiftUI menu bar app
│   ├── Sources/           # Swift source files
│   │   ├── MenuBarApp.swift
│   │   ├── ChatView.swift
│   │   ├── TaskViews.swift
│   │   └── APIClient.swift
│   ├── Package.swift      # Swift Package Manager config
│   └── README.md          # Menu bar app setup guide
├── config/                # Configuration files
│   ├── config.yaml
│   └── credentials.example.yaml
├── scripts/               # Run scripts
│   ├── run_all.sh
│   ├── run_backend.sh
│   ├── run_voice_listener.sh
│   └── run_menu_bar_app.sh
├── data/                  # SQLite database (auto-created)
├── logs/                  # Log files (auto-created)
└── requirements.txt       # Python dependencies
```

## Prerequisites

- Python 3.11+
- macOS (for AppleScript integration)
- Ollama installed and running (for offline LLM)
- OpenAI API key (for online LLM)
- Microsoft Graph API credentials (for Office 365)
- Porcupine access key (for wake word detection)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd AI_Assistant
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Ollama** (for offline mode):
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama3
   ```

5. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and credentials
   ```

6. **Configure settings**:
   ```bash
   # Edit config/config.yaml as needed
   ```

7. **Set up Microsoft Graph API**:
   - Register an app in Azure AD
   - Get client ID, client secret, and tenant ID
   - Add to .env file

## Configuration

### Environment Variables (.env)

```env
# OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Microsoft Graph
MS_CLIENT_ID=your_client_id
MS_CLIENT_SECRET=your_client_secret
MS_TENANT_ID=your_tenant_id
MS_REDIRECT_URI=http://localhost:8000/auth/callback

# Email (IMAP)
EMAIL_IMAP_SERVER=imap.gmail.com
EMAIL_IMAP_PORT=993
EMAIL_IMAP_USERNAME=your_email@gmail.com
EMAIL_IMAP_PASSWORD=your_app_password

# Voice
PORCUPINE_ACCESS_KEY=your_porcupine_key
WAKE_WORD=hey assistant

# Server
SERVER_HOST=localhost
SERVER_PORT=8000

# Database
DATABASE_PATH=./data/assistant.db
```

### Config File (config/config.yaml)

Edit `config/config.yaml` to customize:
- LLM settings (temperature, max tokens)
- Ingestion intervals
- Action keywords for email filtering
- Scheduler intervals

## Usage

### Run All Services

```bash
./scripts/run_all.sh
```

This will:
- Start the FastAPI backend server
- Start background ingestion workers
- Start the voice listener (if enabled)
- Build and launch the menu bar app

### Run Individual Services

**Backend only**:
```bash
./scripts/run_backend.sh
```

**Voice listener only**:
```bash
./scripts/run_voice_listener.sh
```

### Menu Bar App

The menu bar app uses Swift Package Manager. To build and run:

**Option 1: Using Swift Package Manager**
```bash
cd mac-ui
swift build
swift run
```

**Option 2: Using Xcode**
1. Open `mac-ui/Package.swift` in Xcode (File > Open)
2. Or create an Xcode project following `mac-ui/XCODE_SETUP.md`
3. Build and run the app
4. The app will appear in your menu bar
5. Click the icon to open the chat/task interface

For detailed setup instructions, see `mac-ui/README.md` and `mac-ui/QUICK_START.md`.

### API Endpoints

The FastAPI server provides these endpoints:

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /chat` - Chat with AI
- `GET /tasks` - Get tasks
- `GET /tasks/today` - Get today's tasks
- `GET /tasks/overdue` - Get overdue tasks
- `GET /tasks/waiting-on` - Get waiting-on tasks
- `GET /tasks/follow-ups` - Get follow-up tasks
- `POST /tasks` - Create task
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task
- `POST /tasks/extract` - Extract tasks from content
- `POST /actions/execute` - Execute action
- `POST /ingestion/email/scan` - Manually scan emails
- `POST /ingestion/onenote/scan` - Manually scan OneNote
- `GET /status` - Get system status

## Voice Commands

1. Say the wake word: "hey assistant"
2. Wait for confirmation beep
3. Speak your command
4. The assistant will respond via TTS

## Task Extraction

Tasks are automatically extracted from:
- Emails containing action keywords
- OneNote pages
- Manual input via API or menu bar app

Tasks include:
- Title and description
- Due date
- People involved
- Importance (high/medium/low)
- Classification (do/respond/delegate/follow-up/waiting-on)
- Source (email/onenote/manual)

## Actions

The assistant can perform:
- **Create Reminders**: Adds reminders to macOS Reminders app
- **Create Calendar Events**: Adds events to macOS Calendar
- **Create Email Drafts**: Creates drafts in macOS Mail app

## Development

### Project Structure

- `app/` - Python backend code
- `mac-ui/` - SwiftUI menu bar app (source files in `Sources/` directory)
- `config/` - Configuration files
- `scripts/` - Run scripts
- `data/` - SQLite database (created automatically, ignored by git)
- `logs/` - Log files (created automatically, ignored by git)

### Documentation

The project includes comprehensive documentation:
- `README.md` - This file (main project documentation)
- `SETUP.md` - Detailed setup and installation instructions
- `PROJECT_SUMMARY.md` - Complete project overview and component status
- `TESTING_GUIDE.md` - Testing instructions and test results
- `mac-ui/README.md` - Menu bar app setup guide
- `mac-ui/QUICK_START.md` - Quick start for the menu bar app
- `mac-ui/XCODE_SETUP.md` - Xcode project setup instructions
- `AUTO_START_BACKEND.md` - Auto-start backend service guide
- `RUN_APP.md` - Application running instructions
- `VOICE_TESTING.md` - Voice feature testing guide
- `VOICE_TROUBLESHOOTING.md` - Voice feature troubleshooting

### Adding New Features

1. **New Ingestion Source**: Add to `app/ingestion/`
2. **New Action**: Add to `app/actions/`
3. **New Scheduler**: Add to `app/scheduler/`
4. **New API Endpoint**: Add to `app/api/server.py`

## Troubleshooting

### Ollama Not Working
- Ensure Ollama is running: `ollama serve`
- Check model is installed: `ollama list`
- Verify OLLAMA_BASE_URL in .env

### Microsoft Graph Authentication
- Complete OAuth flow via `/auth/callback`
- Check Azure AD app permissions
- Verify credentials in .env

### Voice Not Working
- Check Porcupine access key
- Verify microphone permissions
- Check audio device settings

### Menu Bar App Not Connecting
- Ensure backend is running on localhost:8000
- Check CORS settings in server.py
- Verify network connectivity

## Recent Changes

- **Project Cleanup**: Removed redundant documentation files to streamline the project structure
- **Swift Package Structure**: Menu bar app source files are organized in `mac-ui/Sources/` directory
- **Documentation**: Consolidated and organized all documentation files for easier navigation

## License

[Your License Here]

## Contributing

[Contributing Guidelines]

## Support

For issues and questions:
- Check the troubleshooting section above
- Review the detailed guides in the documentation files
- See `TESTING_GUIDE.md` for testing procedures
- See `VOICE_TROUBLESHOOTING.md` for voice-related issues

