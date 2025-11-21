# Voice Testing Guide

## Prerequisites

Voice functionality requires several components:

1. **PortAudio** (for audio input/output)
2. **Porcupine** (for wake word detection) - requires access key
3. **Whisper** (for speech-to-text)
4. **pyttsx3** (for text-to-speech)

---

## Step 1: Install PortAudio (Required)

PortAudio is needed for `pyaudio` to work:

```bash
# Install using Homebrew
brew install portaudio

# Then install pyaudio
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
source venv/bin/activate
pip install pyaudio
```

---

## Step 2: Get Porcupine Access Key (Optional but Recommended)

Porcupine enables wake word detection ("hey assistant"):

1. **Sign up at Picovoice Console**:
   - Go to: https://console.picovoice.ai
   - Create a free account
   - Get your access key

2. **Add to environment**:
   ```bash
   # Create or edit .env file
   echo "PORCUPINE_ACCESS_KEY=your_access_key_here" >> .env
   echo "WAKE_WORD=hey assistant" >> .env
   ```

**Note**: Without Porcupine, you can still test voice but won't have wake word detection.

---

## Step 3: Verify Dependencies

Check if all voice dependencies are installed:

```bash
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
source venv/bin/activate

# Check pyaudio
python -c "import pyaudio; print('✅ pyaudio installed')" || echo "❌ pyaudio not installed"

# Check whisper
python -c "import whisper; print('✅ whisper installed')" || echo "❌ whisper not installed"

# Check pyttsx3
python -c "import pyttsx3; print('✅ pyttsx3 installed')" || echo "❌ pyttsx3 not installed"

# Check porcupine
python -c "from pvporcupine import Porcupine; print('✅ porcupine installed')" || echo "❌ porcupine not installed"
```

---

## Step 4: Test Voice Listener

### Method 1: Run Voice Listener Standalone

```bash
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
source venv/bin/activate

# Set voice enabled
export VOICE_ENABLED=true
export PORCUPINE_ACCESS_KEY=your_key_here  # If you have one

# Run voice listener
./scripts/run_voice_listener.sh
```

### Method 2: Run with Backend

```bash
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
source venv/bin/activate

# Set environment variables
export VOICE_ENABLED=true
export PORCUPINE_ACCESS_KEY=your_key_here  # If you have one

# Start backend (voice will start automatically)
./scripts/run_backend.sh
```

---

## Step 5: Testing Voice Commands

### With Wake Word Detection (Porcupine)

1. **Start the voice listener** (see Step 4)
2. **Say the wake word**: "Hey Assistant"
3. **Wait for confirmation** (you should hear a beep or see a log message)
4. **Speak your command**: 
   - "What's the weather?"
   - "Create a task to buy groceries"
   - "What are my tasks for today?"
5. **Listen for response**: The assistant will respond via TTS

### Without Wake Word Detection

If Porcupine is not configured, you can test voice in continuous listening mode:

1. The system will continuously listen
2. Speak your command directly
3. Wait for processing
4. Listen for response

---

## Step 6: Test Individual Components

### Test Speech-to-Text (STT)

```bash
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
source venv/bin/activate

python -c "
from app.stt import get_stt_engine
import asyncio

async def test_stt():
    engine = get_stt_engine()
    # Record audio (you'll need to provide audio data)
    # text = await engine.transcribe(audio_data)
    print('STT engine initialized:', engine is not None)

asyncio.run(test_stt())
"
```

### Test Text-to-Speech (TTS)

```bash
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
source venv/bin/activate

python -c "
from app.tts import get_tts_engine

engine = get_tts_engine()
if engine:
    engine.speak('Hello, this is a test of the text to speech engine')
    print('✅ TTS working')
else:
    print('❌ TTS not available')
"
```

### Test Wake Word Detection

```bash
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
source venv/bin/activate

python -c "
import os
from dotenv import load_dotenv
load_dotenv()

from pvporcupine import Porcupine

access_key = os.getenv('PORCUPINE_ACCESS_KEY')
if access_key:
    try:
        porcupine = Porcupine(
            access_key=access_key,
            keywords=['hey assistant'],
            sensitivities=[0.5]
        )
        print('✅ Porcupine initialized successfully')
        porcupine.delete()
    except Exception as e:
        print(f'❌ Porcupine error: {e}')
else:
    print('⚠️  PORCUPINE_ACCESS_KEY not set')
"
```

---

## Step 7: Voice Testing Checklist

- [ ] PortAudio installed (`brew install portaudio`)
- [ ] pyaudio installed (`pip install pyaudio`)
- [ ] Whisper model loaded (check logs)
- [ ] TTS engine initialized (check logs)
- [ ] Porcupine access key set (optional)
- [ ] Microphone permissions granted (System Settings → Privacy → Microphone)
- [ ] Voice listener starts without errors
- [ ] Wake word detected (if Porcupine configured)
- [ ] Speech recognized correctly
- [ ] AI responds to voice commands
- [ ] TTS speaks the response

---

## Troubleshooting

### "No module named 'pyaudio'"
```bash
# Install portaudio first
brew install portaudio

# Then install pyaudio
pip install pyaudio
```

### "PortAudio not found"
```bash
# Install portaudio
brew install portaudio

# Set library path (if needed)
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH
```

### "Porcupine access key not provided"
- This is a warning, not an error
- Voice will work but without wake word detection
- Get a free key from https://console.picovoice.ai

### "Microphone not working"
1. Check System Settings → Privacy → Microphone
2. Make sure your app has microphone permissions
3. Test microphone in other apps first

### "Whisper model not loading"
- Whisper models are downloaded automatically on first use
- Check internet connection
- For offline, ensure model is cached locally

### Voice commands not recognized
- Speak clearly and at normal pace
- Reduce background noise
- Check microphone input levels
- Review STT logs for transcription errors

---

## Expected Behavior

### When Voice Listener Starts:
```
✅ Porcupine initialized successfully (if key provided)
✅ Audio stream initialized
✅ Voice listener started
Listening for wake word: "hey assistant"
```

### When Wake Word Detected:
```
🎤 Wake word detected!
Recording...
```

### When Command Processed:
```
Transcribed: "what are my tasks"
Processing command...
Response: "You have 3 tasks today..."
🔊 Speaking response...
```

---

## Quick Test Script

Save this as `test_voice.sh`:

```bash
#!/bin/bash

cd /Users/himanshu/SourceCode/Personal/AI_Assistant
source venv/bin/activate

echo "🎤 Testing Voice Components..."
echo ""

# Test TTS
echo "1. Testing TTS..."
python -c "
from app.tts import get_tts_engine
engine = get_tts_engine()
if engine:
    print('✅ TTS engine ready')
    engine.speak('TTS test successful')
else:
    print('❌ TTS not available')
"
echo ""

# Test STT
echo "2. Testing STT..."
python -c "
from app.stt import get_stt_engine
engine = get_stt_engine()
print('✅ STT engine ready' if engine else '❌ STT not available')
"
echo ""

# Test Porcupine
echo "3. Testing Porcupine..."
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
from pvporcupine import Porcupine

key = os.getenv('PORCUPINE_ACCESS_KEY')
if key:
    try:
        p = Porcupine(access_key=key, keywords=['hey assistant'], sensitivities=[0.5])
        print('✅ Porcupine ready')
        p.delete()
    except Exception as e:
        print(f'❌ Porcupine error: {e}')
else:
    print('⚠️  Porcupine key not set (optional)')
"
echo ""

# Test Audio
echo "4. Testing Audio..."
python -c "
import pyaudio
p = pyaudio.PyAudio()
print(f'✅ Audio devices available: {p.get_device_count()}')
p.terminate()
" || echo "❌ Audio not available"
echo ""

echo "✅ Voice testing complete!"
```

Make executable and run:
```bash
chmod +x test_voice.sh
./test_voice.sh
```

---

## Next Steps

1. **Install PortAudio**: `brew install portaudio`
2. **Install pyaudio**: `pip install pyaudio`
3. **Get Porcupine key** (optional): https://console.picovoice.ai
4. **Grant microphone permissions**: System Settings → Privacy → Microphone
5. **Run voice listener**: `./scripts/run_voice_listener.sh`
6. **Test wake word**: Say "Hey Assistant"
7. **Test commands**: Speak naturally after wake word

---

**Ready to test voice? Start with installing PortAudio!**

