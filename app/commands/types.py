"""
Command types and models.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel


class CommandType(str, Enum):
    """Command types."""
    WEATHER = "weather"
    TIME = "time"
    DATE = "date"
    STOP = "stop"
    UNKNOWN = "unknown"


class CommandRequest(BaseModel):
    """Command request model."""
    text: str
    command_type: Optional[CommandType] = None


class CommandResponse(BaseModel):
    """Command response model."""
    handled: bool
    response: str
    command_type: Optional[CommandType] = None
    data: Optional[Dict[str, Any]] = None

