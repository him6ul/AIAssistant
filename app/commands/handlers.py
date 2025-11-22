"""
Individual command handlers.
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any, List
import httpx
import os
from dotenv import load_dotenv
from app.commands.types import CommandType, CommandResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Load environment variables
load_dotenv(override=True)


def get_stop_words() -> List[str]:
    """
    Get stop words from environment variable or return defaults.
    
    Returns:
        List of stop words/phrases
    """
    stop_words_env = os.getenv("STOP_WORDS", "").strip()
    if stop_words_env:
        # Split by comma and clean up
        stop_words = [word.strip().lower() for word in stop_words_env.split(",") if word.strip()]
        if stop_words:
            logger.info(f"Using stop words from .env: {stop_words}")
            return stop_words
    
    # Default stop words if not configured
    default_stop_words = [
        "stop",
        "stop listening",
        "stop the assistant",
        "stop jarvis",
        "jarvis stop",
        "shut down",
        "exit",
        "quit"
    ]
    logger.debug(f"Using default stop words: {default_stop_words}")
    return default_stop_words


class WeatherHandler:
    """Handler for weather-related commands."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    def can_handle(self, text: str) -> bool:
        """Check if this handler can process the command."""
        text_lower = text.lower()
        weather_keywords = ["weather", "temperature", "temp", "forecast", "rain", "sunny", "cloudy"]
        return any(keyword in text_lower for keyword in weather_keywords)
    
    async def handle(self, text: str) -> CommandResponse:
        """Handle weather command."""
        # Extract location if mentioned
        location = self._extract_location(text)
        if not location:
            location = os.getenv("DEFAULT_LOCATION", "San Francisco")
        
        if not self.api_key:
            return CommandResponse(
                handled=True,
                response="I can't check the weather right now. Please set OPENWEATHER_API_KEY in your .env file.",
                command_type=CommandType.WEATHER
            )
        
        try:
            # Get weather data
            url = f"{self.base_url}?q={location}&appid={self.api_key}&units=metric"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            # Format response
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            description = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            city = data["name"]
            country = data["sys"].get("country", "")
            
            response_text = (
                f"The weather in {city}, {country} is {description} with a temperature of {temp}°C "
                f"(feels like {feels_like}°C). Humidity is {humidity}%."
            )
            
            return CommandResponse(
                handled=True,
                response=response_text,
                command_type=CommandType.WEATHER,
                data={
                    "location": city,
                    "temperature": temp,
                    "feels_like": feels_like,
                    "description": description,
                    "humidity": humidity
                }
            )
        except httpx.HTTPError as e:
            logger.error(f"Weather API error: {e}")
            return CommandResponse(
                handled=True,
                response=f"I couldn't fetch the weather for {location}. Please check your internet connection or API key.",
                command_type=CommandType.WEATHER
            )
        except Exception as e:
            logger.error(f"Weather handler error: {e}")
            return CommandResponse(
                handled=True,
                response="I encountered an error checking the weather. Please try again later.",
                command_type=CommandType.WEATHER
            )
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location from text."""
        # Simple pattern matching - can be improved
        patterns = [
            r"weather in (.+?)(?:\.|$|\?)",
            r"weather at (.+?)(?:\.|$|\?)",
            r"weather for (.+?)(?:\.|$|\?)",
            r"temperature in (.+?)(?:\.|$|\?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return match.group(1).strip()
        
        return None


class TimeHandler:
    """Handler for time-related commands."""
    
    def can_handle(self, text: str) -> bool:
        """Check if this handler can process the command."""
        text_lower = text.lower()
        time_keywords = ["time", "what time", "current time", "what's the time"]
        return any(keyword in text_lower for keyword in time_keywords)
    
    async def handle(self, text: str) -> CommandResponse:
        """Handle time command."""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%A, %B %d, %Y")
        
        response_text = f"The current time is {time_str} on {date_str}."
        
        return CommandResponse(
            handled=True,
            response=response_text,
            command_type=CommandType.TIME,
            data={
                "time": time_str,
                "date": date_str,
                "timestamp": now.isoformat()
            }
        )


class DateHandler:
    """Handler for date-related commands."""
    
    def can_handle(self, text: str) -> bool:
        """Check if this handler can process the command."""
        text_lower = text.lower()
        date_keywords = ["date", "what date", "current date", "what's the date", "today"]
        return any(keyword in text_lower for keyword in date_keywords)
    
    async def handle(self, text: str) -> CommandResponse:
        """Handle date command."""
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        
        response_text = f"Today is {date_str}."
        
        return CommandResponse(
            handled=True,
            response=response_text,
            command_type=CommandType.DATE,
            data={
                "date": date_str,
                "timestamp": now.isoformat()
            }
        )


class StopHandler:
    """Handler for stop commands."""
    
    def __init__(self):
        """Initialize stop handler with stop words from environment."""
        self.stop_keywords = get_stop_words()
    
    def can_handle(self, text: str) -> bool:
        """Check if this handler can process the command."""
        text_lower = text.lower().strip()
        return any(keyword in text_lower for keyword in self.stop_keywords)
    
    async def handle(self, text: str) -> CommandResponse:
        """Handle stop command."""
        # This will be handled by the voice listener itself
        return CommandResponse(
            handled=True,
            response="Stopping voice listener. Goodbye!",
            command_type=CommandType.STOP,
            data={"action": "stop"}
        )

