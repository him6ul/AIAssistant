#!/bin/bash

# Start voice listener with proper setup

cd "$(dirname "$0")/.."

echo "🎤 Starting Voice Listener..."
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found"
    exit 1
fi

# Set environment variables
export VOICE_ENABLED=true

# Check for Porcupine key
if [ -f ".env" ]; then
    source .env
fi

if [ -z "$PORCUPINE_ACCESS_KEY" ]; then
    echo "⚠️  Warning: PORCUPINE_ACCESS_KEY not set"
    echo "   Voice will work but wake word detection may be limited"
    echo "   Get a free key at: https://console.picovoice.ai"
    echo ""
fi

echo "✅ Starting voice listener..."
echo "📋 Instructions:"
echo "   1. Grant microphone permissions if prompted"
echo "   2. Say 'Hey Assistant' to activate (if Porcupine configured)"
echo "   3. Or speak directly (continuous listening mode)"
echo "   4. Press Ctrl+C to stop"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start voice listener
python -c "
import asyncio
import os
import signal
from app.voice_listener import get_voice_listener

async def main():
    listener = get_voice_listener()
    print('✅ Voice listener initialized')
    print('🎤 Listening for voice commands...')
    print('')
    
    # Handle shutdown
    def signal_handler(sig, frame):
        print('\\n🛑 Stopping voice listener...')
        listener.stop()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await listener.start()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\\n🛑 Voice listener stopped')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
"

