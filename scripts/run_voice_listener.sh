#!/bin/bash

# Run the voice listener service

cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Set voice enabled
export VOICE_ENABLED=true

# Run voice listener (can be integrated into main.py or run separately)
python -c "
import asyncio
from app.voice_listener import get_voice_listener

async def main():
    listener = get_voice_listener()
    await listener.start()

asyncio.run(main())
"

