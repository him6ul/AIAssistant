# Auto-Start Backend Services on Login

This guide shows how to automatically start the backend and voice listener when you log in to your Mac.

## Quick Setup

Run the setup script:

```bash
./scripts/setup_auto_start_backend.sh
```

This will:
- Create a Launch Agent plist file
- Configure it to start backend + voice listener on login
- Load it immediately
- Set up log files

## What Gets Started

The Launch Agent will automatically start:
- ✅ Backend API server (FastAPI on port 8000)
- ✅ Voice listener (if VOICE_ENABLED=true)
- ✅ All background schedulers (email, OneNote, reminders)

## Manual Setup

If you prefer to set it up manually:

### Step 1: Create Launch Agent Plist

Create file: `~/Library/LaunchAgents/com.aipersonalassistant.backend.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aipersonalassistant.backend</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd "/Users/himanshu/SourceCode/Personal/AI_Assistant" && source venv/bin/activate && export VOICE_ENABLED=true && python -m app.main</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/himanshu/SourceCode/Personal/AI_Assistant</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/Users/himanshu/SourceCode/Personal/AI_Assistant/logs/backend.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/himanshu/SourceCode/Personal/AI_Assistant/logs/backend_error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin</string>
        <key>VOICE_ENABLED</key>
        <string>true</string>
    </dict>
</dict>
</plist>
```

**Important**: Update the paths in the plist to match your actual project directory!

### Step 2: Create Logs Directory

```bash
mkdir -p /Users/himanshu/SourceCode/Personal/AI_Assistant/logs
```

### Step 3: Load the Launch Agent

```bash
launchctl load ~/Library/LaunchAgents/com.aipersonalassistant.backend.plist
```

### Step 4: Test

```bash
# Check if it's running
launchctl list | grep aipersonalassistant

# Check logs
tail -f ~/SourceCode/Personal/AI_Assistant/logs/backend.log
```

## Verify It's Working

### Check Status

```bash
# List all launch agents
launchctl list | grep aipersonalassistant

# Check if backend is running
curl http://localhost:8000/health

# Check processes
ps aux | grep "python.*app.main"
```

### View Logs

```bash
# Backend logs
tail -f logs/backend.log

# Error logs
tail -f logs/backend_error.log
```

## Manage the Service

### Start Manually

```bash
launchctl start com.aipersonalassistant.backend
```

### Stop

```bash
launchctl stop com.aipersonalassistant.backend
```

### Unload (Disable Auto-Start)

```bash
launchctl unload ~/Library/LaunchAgents/com.aipersonalassistant.backend.plist
```

### Reload (After Changes)

```bash
launchctl unload ~/Library/LaunchAgents/com.aipersonalassistant.backend.plist
launchctl load ~/Library/LaunchAgents/com.aipersonalassistant.backend.plist
```

### Remove Completely

```bash
launchctl unload ~/Library/LaunchAgents/com.aipersonalassistant.backend.plist
rm ~/Library/LaunchAgents/com.aipersonalassistant.backend.plist
```

## Troubleshooting

### Service Not Starting

1. **Check logs**:
   ```bash
   tail -50 logs/backend_error.log
   ```

2. **Check plist syntax**:
   ```bash
   plutil -lint ~/Library/LaunchAgents/com.aipersonalassistant.backend.plist
   ```

3. **Verify paths**:
   - Make sure project directory path is correct
   - Make sure venv exists
   - Make sure Python is in PATH

### Service Starts But Stops Immediately

- Check error logs: `logs/backend_error.log`
- Verify virtual environment is activated correctly
- Check if port 8000 is already in use
- Verify all dependencies are installed

### Environment Variables Not Working

Add them to the plist's `EnvironmentVariables` dict:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PORCUPINE_ACCESS_KEY</key>
    <string>your_key_here</string>
    <key>OPENAI_API_KEY</key>
    <string>your_key_here</string>
    <!-- Add other env vars as needed -->
</dict>
```

Or load from .env file by modifying the ProgramArguments:

```xml
<key>ProgramArguments</key>
<array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>cd "/path/to/project" && source venv/bin/activate && export \$(cat .env | xargs) && python -m app.main</string>
</array>
```

## Combined Setup (Backend + Menu Bar App)

To auto-start both the backend AND the menu bar app:

1. **Backend**: Use this Launch Agent (already set up)
2. **Menu Bar App**: Use the menu bar app auto-start script:
   ```bash
   cd mac-ui
   ./setup_auto_start.sh
   ```

Both will start automatically on login!

## What Happens on Login

1. ✅ Launch Agent starts backend service
2. ✅ Backend initializes database
3. ✅ Backend starts API server on port 8000
4. ✅ Voice listener starts (if enabled)
5. ✅ Menu bar app starts (if configured)
6. ✅ All services ready to use!

## Log Files

Logs are saved to:
- `logs/backend.log` - Standard output
- `logs/backend_error.log` - Errors

Rotate logs periodically to prevent them from growing too large.

---

**Ready to set up?** Run: `./scripts/setup_auto_start_backend.sh`

