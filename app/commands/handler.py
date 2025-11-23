"""
Command handler - routes commands to appropriate handlers.
"""

from typing import Optional, List
from app.commands.types import CommandRequest, CommandResponse, CommandType
from app.commands.handlers import WeatherHandler, TimeHandler, DateHandler, StopHandler
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CommandHandler:
    """
    Main command handler that routes commands to specific handlers.
    """
    
    def __init__(self):
        """Initialize command handler with all available handlers."""
        self.handlers = [
            StopHandler(),  # Check stop first
            WeatherHandler(),
            TimeHandler(),
            DateHandler(),
        ]
    
    async def process(self, text: str) -> CommandResponse:
        """
        Process a command and return response.
        
        Args:
            text: User input text
            
        Returns:
            CommandResponse indicating if command was handled and the response
        """
        text = text.strip()
        if not text:
            return CommandResponse(
                handled=False,
                response="",
                command_type=CommandType.UNKNOWN
            )
        
        # Try each handler
        logger.debug(f"Processing command: '{text}'")
        for handler in self.handlers:
            logger.debug(f"Checking if {handler.__class__.__name__} can handle: '{text}'")
            if handler.can_handle(text):
                logger.info(f"✅ Command handled by {handler.__class__.__name__}")
                return await handler.handle(text)
            else:
                logger.debug(f"❌ {handler.__class__.__name__} cannot handle: '{text}'")
        
        # No handler matched
        logger.info(f"⚠️  No handler matched command: '{text}'")
        return CommandResponse(
            handled=False,
            response="",
            command_type=CommandType.UNKNOWN
        )


# Global command handler instance
_handler: Optional[CommandHandler] = None


def get_command_handler() -> CommandHandler:
    """
    Get or create the global command handler instance.
    
    Returns:
        CommandHandler instance
    """
    global _handler
    if _handler is None:
        _handler = CommandHandler()
    return _handler

