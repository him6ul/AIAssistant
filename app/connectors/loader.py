"""
Connector loader - initializes and registers all connectors.
"""

from app.connectors.registry import get_connector_registry
from app.connectors.outlook_connector import OutlookConnector
from app.connectors.gmail_connector import GmailConnector
from app.utils.logger import get_logger

logger = get_logger(__name__)


def load_connectors():
    """
    Load and register all available connectors.
    This should be called during application startup.
    """
    registry = get_connector_registry()
    
    # Register all connector classes
    registry.register("outlook", OutlookConnector)
    registry.register("gmail", GmailConnector)
    
    # Add more connectors here as they are implemented
    # registry.register("yahoo", YahooConnector)
    # registry.register("teams", TeamsConnector)
    # registry.register("onenote", OneNoteConnector)
    
    logger.info(f"Loaded {len(registry.list_available())} connector types")


async def initialize_connectors():
    """
    Initialize all configured connectors.
    This should be called during application startup.
    """
    registry = get_connector_registry()
    
    # Initialize connectors based on configuration
    # For now, we'll try to initialize all registered connectors
    # In production, this should be based on config/env vars
    
    connectors_to_init = []
    
    # Check which connectors should be initialized
    import os
    if os.getenv("MS_CLIENT_ID"):  # Outlook
        connectors_to_init.append("outlook")
    if os.getenv("EMAIL_IMAP_USERNAME"):  # Gmail/IMAP
        connectors_to_init.append("gmail")
    
    for connector_name in connectors_to_init:
        try:
            await registry.initialize_connector(connector_name)
        except Exception as e:
            logger.error(f"Failed to initialize connector {connector_name}: {e}")
    
    logger.info(f"Initialized {len(registry.list_initialized())} connectors")

