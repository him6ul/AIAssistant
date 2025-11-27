#!/usr/bin/env python3
"""
Test transcription directly to see what's happening.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.stt import get_stt_engine
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def test_transcription():
    """Test transcription with a simple phrase."""
    stt_engine = get_stt_engine()
    
    # Test with a simple text file (we'll need to record audio first)
    print("\n" + "="*60)
    print("Testing STT Engine")
    print("="*60 + "\n")
    
    print("STT Engine Type:", type(stt_engine).__name__)
    print("Use OpenAI API:", getattr(stt_engine, 'use_openai_api', 'N/A'))
    print("Local Model Available:", getattr(stt_engine, 'local_model', None) is not None)
    print()
    
    # Check if we can create a test audio file
    print("To test transcription, you need to:")
    print("1. Record audio saying 'what is the weather outside'")
    print("2. Save it as test_audio.wav")
    print("3. Run this script again")
    print()
    
    test_file = "test_audio.wav"
    if os.path.exists(test_file):
        print(f"Found {test_file}, testing transcription...")
        result = await stt_engine.transcribe(test_file)
        print(f"Transcription result: '{result}'")
        if result:
            print("✅ Transcription successful!")
        else:
            print("❌ Transcription failed - returned None or empty")
    else:
        print(f"Test audio file '{test_file}' not found.")
        print("You can record audio using:")
        print("  rec -r 16000 -c 1 -b 16 test_audio.wav")


if __name__ == "__main__":
    asyncio.run(test_transcription())

