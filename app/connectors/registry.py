"""
Connector registry - manages all available connectors.
"""

from typing import Dict, List, Optional, Type
from app.connectors.base import BaseConnector, ConnectorType
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectorRegistry:
    """
    Registry for managing connectors.
    Allows easy registration and retrieval of connectors.
    """
    
    def __init__(self):
        """Initialize registry."""
        self._connectors: Dict[str, BaseConnector] = {}
        self._connector_classes: Dict[str, Type[BaseConnector]] = {}
    
    def register(
        self,
        name: str,
        connector_class: Type[BaseConnector],
        auto_init: bool = False
    ):
        """
        Register a connector class.
        
        Args:
            name: Connector name (e.g., "outlook", "gmail")
            connector_class: Connector class
            auto_init: Whether to auto-initialize when registered
        """
        self._connector_classes[name] = connector_class
        logger.info(f"Registered connector: {name}")
        
        if auto_init:
            self.initialize_connector(name)
    
    async def initialize_connector(self, name: str, **kwargs) -> Optional[BaseConnector]:
        """
        Initialize a connector instance.
        
        Args:
            name: Connector name
            **kwargs: Arguments to pass to connector constructor
            
        Returns:
            Initialized connector instance or None if failed
        """
        if name not in self._connector_classes:
            logger.warning(f"Connector {name} not registered")
            return None
        
        try:
            connector_class = self._connector_classes[name]
            connector = connector_class(name=name, **kwargs)
            
            # Initialize the connector (async)
            success = await connector.initialize()
            if not success:
                logger.warning(f"Connector {name} initialization returned False")
                return None
            
            self._connectors[name] = connector
            logger.info(f"Initialized connector: {name}")
            return connector
        except Exception as e:
            logger.error(f"Failed to initialize connector {name}: {e}")
            return None
    
    def get(self, name: str) -> Optional[BaseConnector]:
        """
        Get a connector instance.
        
        Args:
            name: Connector name
            
        Returns:
            Connector instance or None if not found
        """
        return self._connectors.get(name)
    
    def get_all(self, connector_type: Optional[ConnectorType] = None) -> List[BaseConnector]:
        """
        Get all connectors, optionally filtered by type.
        
        Args:
            connector_type: Optional filter by connector type
            
        Returns:
            List of connectors
        """
        if connector_type:
            return [
                connector for connector in self._connectors.values()
                if connector.connector_type == connector_type
            ]
        return list(self._connectors.values())
    
    def list_available(self) -> List[str]:
        """
        List all available connector names.
        
        Returns:
            List of connector names
        """
        return list(self._connector_classes.keys())
    
    def list_initialized(self) -> List[str]:
        """
        List all initialized connector names.
        
        Returns:
            List of initialized connector names
        """
        return list(self._connectors.keys())


# Global registry instance
_registry: Optional[ConnectorRegistry] = None


def get_connector_registry() -> ConnectorRegistry:
    """
    Get or create the global connector registry.
    
    Returns:
        ConnectorRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
    return _registry

