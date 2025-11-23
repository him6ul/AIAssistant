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
        text_lower = text.lower().strip()
        
        # Expanded weather keywords and phrases
        weather_keywords = [
            "weather", "temperature", "temp", "forecast", "rain", "sunny", "cloudy",
            "outside", "outdoor", "climate", "conditions", "how's the weather",
            "what's the weather", "what is the weather", "weather outside",
            "weather today", "current weather", "weather now", "weather report"
        ]
        
        # Check for weather-related phrases
        weather_phrases = [
            "what is the weather",
            "what's the weather",
            "how's the weather",
            "weather outside",
            "weather today",
            "current weather",
            "weather now"
        ]
        
        # Check for phrases first (more specific)
        for phrase in weather_phrases:
            if phrase in text_lower:
                logger.info(f"Weather handler matched phrase: '{phrase}' in '{text}'")
                return True
        
        # Then check for keywords
        matched_keywords = [kw for kw in weather_keywords if kw in text_lower]
        if matched_keywords:
            logger.info(f"Weather handler matched keywords: {matched_keywords} in '{text}'")
            return True
        
        logger.debug(f"Weather handler did not match: '{text}'")
        return False
    
    async def handle(self, text: str) -> CommandResponse:
        """Handle weather command."""
        # Extract location if mentioned
        location = self._extract_location(text)
        if not location:
            # Try to get current location automatically
            use_auto_location = os.getenv("USE_AUTO_LOCATION", "true").lower() == "true"
            if use_auto_location:
                try:
                    from app.utils.location import get_current_location
                    detected_location = await get_current_location()
                    if detected_location:
                        location = detected_location
                        logger.info(f"Using auto-detected location: {location}")
                    else:
                        # Fall back to DEFAULT_LOCATION
                        location = os.getenv("DEFAULT_LOCATION", "San Francisco")
                        logger.info(f"Auto-location failed, using DEFAULT_LOCATION: {location}")
                except Exception as e:
                    logger.warning(f"Auto-location detection failed: {e}, using DEFAULT_LOCATION")
                    location = os.getenv("DEFAULT_LOCATION", "San Francisco")
            else:
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
        text_lower = text.lower()
        
        # Expanded patterns to catch more location mentions
        patterns = [
            r"weather in (.+?)(?:\.|$|\?|outside|today)",
            r"weather at (.+?)(?:\.|$|\?|outside|today)",
            r"weather for (.+?)(?:\.|$|\?|outside|today)",
            r"temperature in (.+?)(?:\.|$|\?|outside|today)",
            r"weather (.+?)(?:\.|$|\?|outside|today)",
            r"in (.+?)(?:\.|$|\?|outside|today)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                location = match.group(1).strip()
                # Filter out common non-location words
                if location and location not in ["outside", "today", "now", "here", "there"]:
                    logger.info(f"Extracted location from text: '{location}'")
                    return location
        
        logger.debug(f"No location extracted from: '{text}'")
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

