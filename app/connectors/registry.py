"""
Connector Registry - Plugin mechanism for managing connectors.

This registry allows dynamic registration and retrieval of connectors
without modifying core assistant logic.
"""

from typing import Dict, Optional, Type, Any
from app.connectors.base import (
    MessageSourceConnector,
    MailSourceConnector,
    NoteSourceConnector,
)
from app.connectors.models import SourceType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectorRegistry:
    """
    Central registry for all connectors.
    
    Supports dynamic registration and retrieval of connectors by source type.
    All connectors are registered here and accessed through this registry.
    """
    
    _instance: Optional['ConnectorRegistry'] = None
    _message_connectors: Dict[SourceType, MessageSourceConnector] = {}
    _mail_connectors: Dict[SourceType, MailSourceConnector] = {}
    _note_connectors: Dict[SourceType, NoteSourceConnector] = {}
    
    def __new__(cls):
        """Singleton pattern - ensure only one registry instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_message_connector(
        self,
        source_type: SourceType,
        connector: MessageSourceConnector,
    ) -> None:
        """
        Register a message connector.
        
        Args:
            source_type: The source type this connector handles
            connector: The connector instance
        """
        if source_type in self._message_connectors:
            logger.warning(f"Overwriting existing message connector for {source_type}")
        self._message_connectors[source_type] = connector
        logger.info(f"Registered message connector: {source_type}")
    
    def register_mail_connector(
        self,
        source_type: SourceType,
        connector: MailSourceConnector,
    ) -> None:
        """
        Register a mail connector.
        
        Args:
            source_type: The source type this connector handles
            connector: The connector instance
        """
        if source_type in self._mail_connectors:
            logger.warning(f"Overwriting existing mail connector for {source_type}")
        self._mail_connectors[source_type] = connector
        logger.info(f"Registered mail connector: {source_type}")
    
    def register_note_connector(
        self,
        source_type: SourceType,
        connector: NoteSourceConnector,
    ) -> None:
        """
        Register a note connector.
        
        Args:
            source_type: The source type this connector handles
            connector: The connector instance
        """
        if source_type in self._note_connectors:
            logger.warning(f"Overwriting existing note connector for {source_type}")
        self._note_connectors[source_type] = connector
        logger.info(f"Registered note connector: {source_type}")
    
    def get_message_connector(
        self,
        source_type: SourceType,
    ) -> Optional[MessageSourceConnector]:
        """
        Get a message connector by source type.
        
        Args:
            source_type: The source type to get connector for
        
        Returns:
            Connector instance or None if not found
        """
        return self._message_connectors.get(source_type)
    
    def get_mail_connector(
        self,
        source_type: SourceType,
    ) -> Optional[MailSourceConnector]:
        """
        Get a mail connector by source type.
        
        Args:
            source_type: The source type to get connector for
        
        Returns:
            Connector instance or None if not found
        """
        return self._mail_connectors.get(source_type)
    
    def get_note_connector(
        self,
        source_type: SourceType,
    ) -> Optional[NoteSourceConnector]:
        """
        Get a note connector by source type.
        
        Args:
            source_type: The source type to get connector for
        
        Returns:
            Connector instance or None if not found
        """
        return self._note_connectors.get(source_type)
    
    def get_all_message_connectors(self) -> Dict[SourceType, MessageSourceConnector]:
        """Get all registered message connectors."""
        return self._message_connectors.copy()
    
    def get_all_mail_connectors(self) -> Dict[SourceType, MailSourceConnector]:
        """Get all registered mail connectors."""
        return self._mail_connectors.copy()
    
    def get_all_note_connectors(self) -> Dict[SourceType, NoteSourceConnector]:
        """Get all registered note connectors."""
        return self._note_connectors.copy()
    
    def unregister_connector(self, source_type: SourceType) -> None:
        """
        Unregister a connector (any type).
        
        Args:
            source_type: The source type to unregister
        """
        removed = False
        if source_type in self._message_connectors:
            del self._message_connectors[source_type]
            removed = True
        if source_type in self._mail_connectors:
            del self._mail_connectors[source_type]
            removed = True
        if source_type in self._note_connectors:
            del self._note_connectors[source_type]
            removed = True
        
        if removed:
            logger.info(f"Unregistered connector: {source_type}")
        else:
            logger.warning(f"No connector found to unregister: {source_type}")
    
    def is_registered(self, source_type: SourceType) -> bool:
        """
        Check if a connector is registered for the given source type.
        
        Args:
            source_type: The source type to check
        
        Returns:
            True if registered, False otherwise
        """
        return (
            source_type in self._message_connectors or
            source_type in self._mail_connectors or
            source_type in self._note_connectors
        )
    
    def get_registered_types(self) -> list[SourceType]:
        """Get list of all registered source types."""
        all_types = set()
        all_types.update(self._message_connectors.keys())
        all_types.update(self._mail_connectors.keys())
        all_types.update(self._note_connectors.keys())
        return list(all_types)
    
    def clear(self) -> None:
        """Clear all registered connectors (useful for testing)."""
        self._message_connectors.clear()
        self._mail_connectors.clear()
        self._note_connectors.clear()
        logger.info("Cleared all connectors from registry")


# Global registry instance
_registry: Optional[ConnectorRegistry] = None


def get_registry() -> ConnectorRegistry:
    """Get the global connector registry instance."""
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
    return _registry
