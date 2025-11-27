#!/usr/bin/env python3
"""
Test script to verify weather command handling.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.commands.handler import get_command_handler
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def test_weather_commands():
    """Test various weather command phrasings."""
    handler = get_command_handler()
    
    test_phrases = [
        "what is the weather outside",
        "what's the weather outside",
        "weather outside",
        "what is the weather",
        "weather today",
        "current weather",
        "how's the weather",
    ]
    
    print("\n" + "="*60)
    print("Testing Weather Command Handler")
    print("="*60 + "\n")
    
    for phrase in test_phrases:
        print(f"Testing: '{phrase}'")
        print("-" * 60)
        
        response = await handler.process(phrase)
        
        if response.handled:
            print(f"✅ HANDLED by {response.command_type}")
            print(f"Response: {response.response[:100]}..." if len(response.response) > 100 else response.response)
        else:
            print(f"❌ NOT HANDLED")
            print(f"Command type: {response.command_type}")
        
        print()
    
    print("="*60)
    print("Test Complete")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_weather_commands())

