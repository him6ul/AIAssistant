"""
Base connector interface for all communication service connectors.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class ConnectorType(str, Enum):
    """Types of connectors."""
    EMAIL = "email"
    CALENDAR = "calendar"
    NOTES = "notes"
    MESSAGING = "messaging"
    TASKS = "tasks"


class Message(BaseModel):
    """Generic message model."""
    id: str
    subject: Optional[str] = None
    body: str
    sender: Optional[str] = None
    recipient: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class BaseConnector(ABC):
    """
    Base class for all connectors.
    Each connector must implement these methods.
    """
    
    def __init__(self, name: str, connector_type: ConnectorType):
        """
        Initialize connector.
        
        Args:
            name: Connector name (e.g., "outlook", "gmail")
            connector_type: Type of connector
        """
        self.name = name
        self.connector_type = connector_type
        self.initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the connector (authenticate, setup, etc.).
        
        Returns:
            True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if connector is available and configured.
        
        Returns:
            True if available, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_messages(
        self,
        limit: int = 50,
        unread_only: bool = False,
        since: Optional[datetime] = None
    ) -> List[Message]:
        """
        Get messages from the service.
        
        Args:
            limit: Maximum number of messages to retrieve
            unread_only: Only get unread messages
            since: Only get messages since this datetime
            
        Returns:
            List of messages
        """
        pass
    
    @abstractmethod
    async def send_message(
        self,
        to: str,
        subject: Optional[str],
        body: str,
        **kwargs
    ) -> bool:
        """
        Send a message.
        
        Args:
            to: Recipient address
            subject: Message subject (if applicable)
            body: Message body
            **kwargs: Additional parameters
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get connector information.
        
        Returns:
            Dictionary with connector info
        """
        return {
            "name": self.name,
            "type": self.connector_type.value,
            "initialized": self.initialized,
            "available": False  # Will be set by is_available()
        }

