"""
Plugin-based connector architecture for email and communication services.
"""

from app.connectors.base import BaseConnector, ConnectorType
from app.connectors.registry import ConnectorRegistry, get_connector_registry

__all__ = [
    "BaseConnector",
    "ConnectorType",
    "ConnectorRegistry",
    "get_connector_registry"
]

