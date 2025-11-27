#!/usr/bin/env python3
"""
Test the full voice command flow for weather queries.
This simulates what happens when you ask "what is the weather outside"
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.commands.handler import get_command_handler
from app.voice_listener import VoiceListener
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def test_weather_via_command_handler():
    """Test weather command through command handler (simulating successful transcription)."""
    print("\n" + "="*60)
    print("TEST 1: Weather Command Handler (Direct Text)")
    print("="*60 + "\n")
    
    handler = get_command_handler()
    test_phrase = "what is the weather outside"
    
    print(f"Testing phrase: '{test_phrase}'")
    response = await handler.process(test_phrase)
    
    if response.handled:
        print(f"✅ HANDLED by {response.command_type}")
        print(f"Response: {response.response}")
        return True
    else:
        print(f"❌ NOT HANDLED")
        return False


async def test_transcription_simulation():
    """Simulate what happens when audio is transcribed."""
    print("\n" + "="*60)
    print("TEST 2: Transcription Simulation")
    print("="*60 + "\n")
    
    # Simulate different transcription results
    test_cases = [
        ("what is the weather outside", True),
        ("what's the weather outside", True),
        ("weather outside", True),
        ("", False),  # Empty transcription
        ("w", False),  # Too short
        ("what", False),  # Incomplete
    ]
    
    handler = get_command_handler()
    
    for text, should_handle in test_cases:
        print(f"\nTesting transcription: '{text}'")
        if not text:
            print("  ⚠️  Empty transcription - would trigger 'I didn't catch that'")
            continue
        
        if len(text) < 3:
            print(f"  ⚠️  Too short ({len(text)} chars) - would trigger warning")
            continue
        
        response = await handler.process(text)
        if response.handled == should_handle:
            print(f"  ✅ Expected behavior")
        else:
            print(f"  ❌ Unexpected behavior (handled={response.handled}, expected={should_handle})")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("VOICE WEATHER COMMAND TEST SUITE")
    print("="*60)
    
    # Test 1: Direct command handler
    test1_result = await test_weather_via_command_handler()
    
    # Test 2: Transcription simulation
    await test_transcription_simulation()
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Command Handler Test: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print("\nNext Steps:")
    print("1. Check logs when you ask 'what is the weather outside'")
    print("2. Look for 'Transcribing audio bytes' in logs")
    print("3. Check if transcription returns text or None")
    print("4. Verify audio duration is > 0.1 seconds")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

