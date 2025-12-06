#!/bin/bash

# Start the AI Assistant (backend + voice listener)
# This script ensures the assistant is always running

cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ensure .env has required settings
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Creating basic .env file..."
    touch .env
    echo "VOICE_ENABLED=true" >> .env
    echo "WAKE_WORD=jarvis" >> .env
    echo "USER_NAME=Himanshu" >> .env
fi

# Check if VOICE_ENABLED is set
if ! grep -q "VOICE_ENABLED=true" .env 2>/dev/null; then
    echo "⚠️  Setting VOICE_ENABLED=true in .env..."
    if ! grep -q "VOICE_ENABLED" .env 2>/dev/null; then
        echo "VOICE_ENABLED=true" >> .env
    else
        sed -i '' 's/^VOICE_ENABLED=.*/VOICE_ENABLED=true/' .env
    fi
fi

# Check if WAKE_WORD is set
if ! grep -q "WAKE_WORD=" .env 2>/dev/null; then
    echo "⚠️  Setting WAKE_WORD=jarvis in .env..."
    echo "WAKE_WORD=jarvis" >> .env
fi

# Check if USER_NAME is set
if ! grep -q "USER_NAME=" .env 2>/dev/null; then
    echo "⚠️  Setting USER_NAME=Himanshu in .env..."
    echo "USER_NAME=Himanshu" >> .env
fi

# Export environment variables
export VOICE_ENABLED=true
export WAKE_WORD=jarvis
export USER_NAME=Himanshu

# Load .env if it exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "🚀 Starting AI Assistant..."
echo "   - Voice enabled: $VOICE_ENABLED"
echo "   - Wake word: $WAKE_WORD"
echo "   - User name: $USER_NAME"
echo ""

# Run the server (this will start voice listener if VOICE_ENABLED=true)
python -m app.main

