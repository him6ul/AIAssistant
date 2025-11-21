#!/bin/bash

# Setup script for voice functionality

cd "$(dirname "$0")/.."

echo "🎤 Setting up Voice Functionality..."
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found"
    echo "   Please install Homebrew first: https://brew.sh"
    exit 1
fi

echo "✅ Homebrew found"
echo ""

# Check if portaudio is installed
if brew list portaudio &> /dev/null; then
    echo "✅ PortAudio already installed"
else
    echo "📦 Installing PortAudio..."
    brew install portaudio
    if [ $? -eq 0 ]; then
        echo "✅ PortAudio installed successfully"
    else
        echo "❌ Failed to install PortAudio"
        exit 1
    fi
fi

echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found"
    echo "   Run: python3 -m venv venv && source venv/bin/activate"
    exit 1
fi

echo ""

# Install pyaudio
echo "📦 Installing pyaudio..."
pip install pyaudio

if [ $? -eq 0 ]; then
    echo "✅ pyaudio installed successfully"
else
    echo "❌ Failed to install pyaudio"
    echo "   Make sure PortAudio is installed: brew install portaudio"
    exit 1
fi

echo ""

# Check other voice dependencies
echo "📦 Checking voice dependencies..."

# Check whisper
python -c "import whisper" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ whisper installed"
else
    echo "⚠️  whisper not installed (will be downloaded on first use)"
fi

# Check pyttsx3
python -c "import pyttsx3" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ pyttsx3 installed"
else
    echo "📦 Installing pyttsx3..."
    pip install pyttsx3
fi

# Check porcupine
python -c "from pvporcupine import Porcupine" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ pvporcupine installed"
else
    echo "📦 Installing pvporcupine..."
    pip install pvporcupine
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Voice setup complete!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Get Porcupine access key (optional but recommended):"
echo "   https://console.picovoice.ai"
echo ""
echo "2. Add to .env file:"
echo "   PORCUPINE_ACCESS_KEY=your_key_here"
echo "   WAKE_WORD=hey assistant"
echo "   VOICE_ENABLED=true"
echo ""
echo "3. Grant microphone permissions:"
echo "   System Settings → Privacy & Security → Microphone"
echo ""
echo "4. Test voice:"
echo "   ./scripts/run_voice_listener.sh"
echo ""

