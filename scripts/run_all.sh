#!/bin/bash

# Run all services: backend, voice listener, and menu bar app

cd "$(dirname "$0")/.."

echo "Starting AI Personal Assistant..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Create necessary directories
mkdir -p data logs

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Please create one from .env.example"
    echo "Copying .env.example to .env..."
    cp .env.example .env 2>/dev/null || echo "Please create .env file manually"
fi

# Start backend in background
echo "Starting backend server..."
python -m app.main &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start voice listener if enabled
if [ "${VOICE_ENABLED:-false}" = "true" ]; then
    echo "Starting voice listener..."
    export VOICE_ENABLED=true
    python -c "
import asyncio
from app.voice_listener import get_voice_listener

async def main():
    listener = get_voice_listener()
    await listener.start()

asyncio.run(main())
" &
    VOICE_PID=$!
else
    echo "Voice listener disabled (set VOICE_ENABLED=true to enable)"
fi

# Build and run menu bar app (if Xcode project exists)
if [ -d "mac-ui/MenuBarApp.xcodeproj" ]; then
    echo "Building menu bar app..."
    cd mac-ui
    xcodebuild -project MenuBarApp.xcodeproj -scheme MenuBarApp -configuration Release build
    if [ $? -eq 0 ]; then
        echo "Menu bar app built successfully"
        # Note: To run the app, you'll need to open it from Xcode or build and install it
        echo "To run the menu bar app, open MenuBarApp.xcodeproj in Xcode and run it"
    fi
    cd ..
else
    echo "Menu bar app Xcode project not found. Please create it manually or use Swift Package Manager."
fi

echo ""
echo "Backend server is running (PID: $BACKEND_PID)"
echo "API available at: http://localhost:8000"
echo ""
echo "To stop all services, run: kill $BACKEND_PID ${VOICE_PID:-}"

# Wait for user interrupt
trap "echo 'Stopping services...'; kill $BACKEND_PID ${VOICE_PID:-} 2>/dev/null; exit" INT TERM

wait

