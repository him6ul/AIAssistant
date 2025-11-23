"""
Localization utility for loading localized messages.
"""

import os
from pathlib import Path
from typing import Dict, Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Cache for loaded messages
_message_cache: Optional[Dict[str, str]] = None


def load_localized_messages(locale: str = "en_us") -> Dict[str, str]:
    """
    Load localized messages from file.
    
    Args:
        locale: Locale code (e.g., "en_us")
    
    Returns:
        Dictionary of message keys to values
    """
    global _message_cache
    
    if _message_cache is not None:
        return _message_cache
    
    messages = {}
    config_dir = Path(__file__).parent.parent.parent / "config"
    messages_file = config_dir / f"localized_messages_{locale}.txt"
    
    if not messages_file.exists():
        logger.warning(f"Localized messages file not found: {messages_file}")
        return messages
    
    try:
        with open(messages_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Parse KEY=value format
                if "=" in line:
                    key, value = line.split("=", 1)
                    messages[key.strip()] = value.strip()
        
        logger.info(f"Loaded {len(messages)} localized messages from {messages_file}")
        _message_cache = messages
    except Exception as e:
        logger.error(f"Error loading localized messages: {e}")
    
    return messages


def get_message(key: str, **kwargs) -> str:
    """
    Get a localized message with optional formatting.
    
    Args:
        key: Message key
        **kwargs: Variables to substitute in the message
    
    Returns:
        Formatted message string
    """
    messages = load_localized_messages()
    message = messages.get(key, key)
    
    # Substitute variables
    if kwargs:
        try:
            message = message.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing variable {e} in message {key}")
    
    return message


def clear_cache():
    """Clear the message cache (useful for testing or reloading)."""
    global _message_cache
    _message_cache = None

