# Voice Listener Troubleshooting

## Why "Hey Assistant" Didn't Work

The voice listener needs to be **running** before it can hear you. It's not automatically started with the backend.

## How to Start Voice Listener

### Method 1: Use the Start Script (Easiest)
```bash
./scripts/start_voice.sh
```

### Method 2: Manual Start
```bash
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
source venv/bin/activate
export VOICE_ENABLED=true
./scripts/run_voice_listener.sh
```

### Method 3: Start with Backend
```bash
export VOICE_ENABLED=true
./scripts/run_backend.sh
```

## Check if Voice Listener is Running

```bash
ps aux | grep voice_listener | grep -v grep
```

If you see a process, it's running. If not, start it using one of the methods above.

## Common Issues

### 1. "Nothing happens when I say Hey Assistant"
- **Cause**: Voice listener is not running
- **Solution**: Start it using `./scripts/start_voice.sh`

### 2. "Microphone permission denied"
- **Cause**: macOS hasn't granted microphone access
- **Solution**: 
  - System Settings → Privacy & Security → Microphone
  - Enable access for Terminal or Python

### 3. "Porcupine access key not provided"
- **Cause**: Wake word detection not configured
- **Solution**: 
  - Get free key: https://console.picovoice.ai
  - Add to `.env`: `PORCUPINE_ACCESS_KEY=your_key`

### 4. "No STT engine available"
- **Cause**: Whisper not installed (Python 3.14 compatibility issue)
- **Solution**: 
  - The system will use OpenAI Whisper API if you have an API key
  - Or wait for Whisper Python 3.14 support
  - Current workaround: Uses OpenAI API when online

## Testing Voice

1. **Start the voice listener**:
   ```bash
   ./scripts/start_voice.sh
   ```

2. **Wait for confirmation**:
   - You should see: "✅ Voice listener initialized"
   - "🎤 Listening for voice commands..."

3. **Say the wake word**:
   - "Hey Assistant" (if Porcupine configured)
   - Or speak directly (continuous mode)

4. **Speak your command**:
   - "What are my tasks?"
   - "Create a task to buy groceries"
   - "What's the weather?"

5. **Listen for response**:
   - The AI will respond via text-to-speech

## Verify It's Working

Check the terminal output for:
- ✅ "Voice listener initialized"
- ✅ "Audio stream initialized"
- ✅ "Wake word detected!" (when you say it)
- ✅ "Transcribed: [your command]"
- ✅ "Speaking response..."

## Keep Voice Listener Running

The voice listener runs in the terminal. To keep it running:
- Don't close the terminal
- Or run it in the background:
  ```bash
  nohup ./scripts/start_voice.sh > voice.log 2>&1 &
  ```

## Stop Voice Listener

Press `Ctrl+C` in the terminal where it's running, or:
```bash
pkill -f voice_listener
```

