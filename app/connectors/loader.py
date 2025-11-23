"""
Connector loader - initializes and registers all connectors.
"""

import os
from app.connectors.registry import get_registry
from app.connectors.models import SourceType
from app.connectors.implementations import (
    OutlookConnector,
    GmailConnector,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


def load_connectors():
    """
    Load and register all enabled connectors.
    This should be called during application startup.
    """
    registry = get_registry()
    
    # Check which connectors are enabled
    enable_outlook = os.getenv("ENABLE_OUTLOOK", "false").lower() == "true"
    enable_gmail = os.getenv("ENABLE_GMAIL", "false").lower() == "true"
    
    # Register enabled connectors
    if enable_outlook:
        outlook = OutlookConnector()
        registry.register_mail_connector(SourceType.OUTLOOK, outlook)
        logger.info("Registered Outlook connector")
    
    if enable_gmail:
        gmail = GmailConnector()
        registry.register_mail_connector(SourceType.GMAIL, gmail)
        logger.info("Registered Gmail connector")
    
    logger.info(f"Loaded {len(registry.get_registered_types())} connector type(s)")


async def initialize_connectors():
    """
    Initialize all configured connectors.
    This should be called during application startup.
    """
    registry = get_registry()
    
    # Get all registered connectors
    all_connectors = []
    all_connectors.extend(registry.get_all_mail_connectors().values())
    all_connectors.extend(registry.get_all_message_connectors().values())
    all_connectors.extend(registry.get_all_note_connectors().values())
    
    success_count = 0
    for connector in all_connectors:
        try:
            if await connector.connect():
                success_count += 1
                logger.info(f"Connected {connector.source_type.value} connector")
            else:
                logger.warning(f"Failed to connect {connector.source_type.value} connector")
        except Exception as e:
            logger.error(f"Error connecting {connector.source_type.value} connector: {e}")
    
    logger.info(f"Initialized {success_count} connector(s)")

