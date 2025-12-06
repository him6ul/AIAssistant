# AI Assistant Usage Guide

## Quick Start

The assistant is designed to be always running and respond to voice commands.

### Starting the Assistant

**Option 1: Manual Start**
```bash
./scripts/start_assistant.sh
```

**Option 2: Auto-Start on Login**
```bash
./scripts/setup_auto_start_backend.sh
```

This will configure the assistant to automatically start when you log in to your Mac.

### Using the Assistant

1. **Wake Word**: Say **"Jarvis"** to activate the assistant
   - The assistant will respond with "Yes?" and start listening

2. **Ask Questions**: After saying "Jarvis", you can ask questions like:
   - "What is the weather outside?"
   - "Do I have any meetings today in Google Calendar?"
   - Any other question or command

3. **Stop Command**: Say **"Jarvis Stop"** or **"Stop"** to stop the assistant
   - The assistant will immediately say "Goodbye Himanshu" and stop listening

### Configuration

The assistant uses these environment variables (set in `.env` file):

- `VOICE_ENABLED=true` - Enable voice listening
- `WAKE_WORD=jarvis` - Wake word (default: "jarvis")
- `USER_NAME=Himanshu` - Your name for personalized messages (default: "Himanshu")
- `PORCUPINE_ACCESS_KEY=...` - Required for wake word detection

### Features

- **Always Listening**: The assistant continuously listens for the wake word "Jarvis"
- **Immediate Stop**: Saying "Jarvis Stop" immediately interrupts any ongoing speech and says goodbye
- **Voice Commands**: Supports weather, calendar, and other commands via voice
- **Email Notifications**: Can notify you about important emails (if configured)

### Troubleshooting

**Assistant not responding?**
- Check if the backend is running: `ps aux | grep "python.*main"`
- Check logs: `tail -f logs/backend.log`

**Wake word not detected?**
- Ensure `PORCUPINE_ACCESS_KEY` is set in `.env`
- Check microphone permissions in System Settings

**Stop command not working?**
- The stop command should work even while Jarvis is speaking
- Try saying "Jarvis Stop" or just "Stop"

### Auto-Start Status

Check if auto-start is enabled:
```bash
launchctl list | grep com.aipersonalassistant.backend
```

Start the service manually:
```bash
launchctl start com.aipersonalassistant.backend
```

Stop the service:
```bash
launchctl unload ~/Library/LaunchAgents/com.aipersonalassistant.backend.plist
```

