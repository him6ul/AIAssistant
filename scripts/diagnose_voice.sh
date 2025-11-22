#!/bin/bash

# Voice listener diagnostic script

cd "$(dirname "$0")/.."

echo "🔍 Voice Listener Diagnostic"
echo "============================"
echo ""

# Check Porcupine key
echo "1. Checking Porcupine Access Key..."
if grep -q "PORCUPINE_ACCESS_KEY" .env 2>/dev/null; then
    KEY=$(grep "PORCUPINE_ACCESS_KEY" .env | cut -d'=' -f2 | head -1)
    if [ -z "$KEY" ] || [ "$KEY" = "your_porcupine_access_key_here" ]; then
        echo "   ❌ Porcupine key not set or using placeholder"
    else
        echo "   ✅ Porcupine key is set"
    fi
else
    echo "   ❌ PORCUPINE_ACCESS_KEY not found in .env"
fi

# Check wake word
echo ""
echo "2. Checking Wake Word Configuration..."
WAKE_WORD=$(grep "WAKE_WORD" .env 2>/dev/null | cut -d'=' -f2 | head -1 | tr -d '"' | tr -d "'")
if [ -z "$WAKE_WORD" ]; then
    echo "   ⚠️  WAKE_WORD not set, using default: 'hey assistant'"
    WAKE_WORD="hey assistant"
else
    echo "   ✅ Wake word is set to: '$WAKE_WORD'"
fi

# Check if voice listener is running
echo ""
echo "3. Checking if Voice Listener is Running..."
if ps aux | grep -E "voice_listener|python.*get_voice_listener" | grep -v grep > /dev/null; then
    echo "   ✅ Voice listener is running"
    ps aux | grep -E "voice_listener|python.*get_voice_listener" | grep -v grep | head -1
else
    echo "   ❌ Voice listener is NOT running"
    echo "   💡 Start it with: ./scripts/start_voice.sh"
fi

# Check microphone permissions (macOS)
echo ""
echo "4. Checking Microphone Permissions..."
if [ "$(uname)" = "Darwin" ]; then
    echo "   ℹ️  On macOS, check System Settings → Privacy & Security → Microphone"
    echo "   ℹ️  Make sure Terminal or Python has microphone access"
fi

# Check Python dependencies
echo ""
echo "5. Checking Python Dependencies..."
source venv/bin/activate 2>/dev/null || true

python3 -c "import pvporcupine; print('   ✅ pvporcupine installed')" 2>/dev/null || echo "   ❌ pvporcupine not installed"
python3 -c "import pyaudio; print('   ✅ pyaudio installed')" 2>/dev/null || echo "   ❌ pyaudio not installed"
python3 -c "import whisper; print('   ✅ whisper installed')" 2>/dev/null || echo "   ⚠️  whisper not installed (will use OpenAI API)"
python3 -c "import pyttsx3; print('   ✅ pyttsx3 installed')" 2>/dev/null || echo "   ❌ pyttsx3 not installed"

# Summary
echo ""
echo "============================"
echo "📋 Summary:"
echo ""
echo "To use 'Hey Jarvis', you can:"
echo "  1. Set WAKE_WORD=jarvis in .env (recommended)"
echo "  2. Or set WAKE_WORD='hey jarvis' in .env"
echo "  3. Or keep 'hey assistant' - it maps to 'jarvis' keyword"
echo ""
echo "The code now supports:"
echo "  - 'hey assistant' → uses 'jarvis' keyword"
echo "  - 'jarvis' → uses 'jarvis' keyword"
echo "  - 'hey jarvis' → uses 'jarvis' keyword"
echo ""
echo "After changing .env, restart the voice listener:"
echo "  ./scripts/start_voice.sh"

