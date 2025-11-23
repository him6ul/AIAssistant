"""
Concrete connector implementations.

Each connector implements the base interfaces and handles
platform-specific API interactions.
"""

from app.connectors.implementations.outlook_connector import OutlookConnector
from app.connectors.implementations.gmail_connector import GmailConnector

__all__ = [
    "OutlookConnector",
    "GmailConnector",
]

