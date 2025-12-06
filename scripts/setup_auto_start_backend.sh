#!/bin/bash

# Setup script to auto-start backend and voice listener on login

cd "$(dirname "$0")/.."

PROJECT_DIR="$(pwd)"
PLIST_NAME="com.aipersonalassistant.backend"
PLIST_FILE="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

echo "🚀 Setting up Auto-Start for Backend Services..."
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Creating basic .env file..."
    touch .env
    echo "VOICE_ENABLED=true" >> .env
fi

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$HOME/Library/LaunchAgents"

# Create the plist file
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cd "${PROJECT_DIR}" && source venv/bin/activate && export VOICE_ENABLED=true && export WAKE_WORD=jarvis && export USER_NAME=Himanshu && python -m app.main</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>${PROJECT_DIR}/logs/backend.log</string>
    
    <key>StandardErrorPath</key>
    <string>${PROJECT_DIR}/logs/backend_error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin</string>
        <key>VOICE_ENABLED</key>
        <string>true</string>
        <key>WAKE_WORD</key>
        <string>jarvis</string>
        <key>USER_NAME</key>
        <string>Himanshu</string>
    </dict>
</dict>
</plist>
EOF

echo "✅ Created Launch Agent plist: $PLIST_FILE"
echo ""

# Create logs directory
mkdir -p "${PROJECT_DIR}/logs"

# Load the launch agent
echo "📦 Loading Launch Agent..."
launchctl unload "$PLIST_FILE" 2>/dev/null
launchctl load "$PLIST_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Launch Agent loaded successfully!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Log out and log back in to test"
    echo "   2. Or test now: launchctl start ${PLIST_NAME}"
    echo ""
    echo "🔍 Check status:"
    echo "   launchctl list | grep ${PLIST_NAME}"
    echo ""
    echo "📄 View logs:"
    echo "   tail -f ${PROJECT_DIR}/logs/backend.log"
    echo ""
    echo "🛑 To stop:"
    echo "   launchctl unload ~/Library/LaunchAgents/${PLIST_NAME}.plist"
    echo ""
    echo "🗑️  To remove:"
    echo "   launchctl unload ~/Library/LaunchAgents/${PLIST_NAME}.plist"
    echo "   rm ~/Library/LaunchAgents/${PLIST_NAME}.plist"
else
    echo "❌ Failed to load Launch Agent"
    echo "   Check the plist file for errors"
    exit 1
fi

