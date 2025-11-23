"""
Microsoft Teams connector implementation using Microsoft Graph API.
"""

import os
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
from app.connectors.base import MessageSourceConnector, ConnectorCapabilities
from app.connectors.models import UnifiedMessage, SourceType
from app.connectors.middleware import with_retry, RetryConfig, with_error_boundary, with_logging
from app.ingestion.ms_graph_client import get_graph_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TeamsConnector(MessageSourceConnector):
    """
    Microsoft Teams connector using Microsoft Graph API.
    
    This connector implements the MessageSourceConnector interface
    and converts Teams-specific data to UnifiedMessage format.
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize Teams connector.
        
        Args:
            client_id: Microsoft Azure AD client ID
            client_secret: Microsoft Azure AD client secret
            tenant_id: Microsoft Azure AD tenant ID
        """
        self.client_id = client_id or os.getenv("MS_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("MS_CLIENT_SECRET")
        self.tenant_id = tenant_id or os.getenv("MS_TENANT_ID")
        self._graph_client = None
        self._connected = False
        self._event_callbacks: List[Callable[[UnifiedMessage], None]] = []
        
        self._retry_config = RetryConfig(max_retries=3, initial_delay=1.0)
    
    @property
    def source_type(self) -> SourceType:
        """Return Teams source type."""
        return SourceType.TEAMS
    
    @with_logging()
    @with_retry(RetryConfig(max_retries=3))
    async def connect(self) -> bool:
        """Connect to Microsoft Graph API."""
        try:
            if not all([self.client_id, self.client_secret, self.tenant_id]):
                logger.error("Teams credentials not configured")
                return False
            
            # Use existing MS Graph client
            from app.ingestion.ms_graph_client import MSGraphClient
            self._graph_client = MSGraphClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                tenant_id=self.tenant_id,
            )
            
            # Test connection
            await self._graph_client.get_access_token()
            self._connected = True
            logger.info("Teams connector connected successfully")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Teams: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Microsoft Graph API."""
        self._graph_client = None
        self._connected = False
        logger.info("Teams connector disconnected")
    
    @with_error_boundary("Failed to fetch Teams messages", return_on_error=[])
    @with_logging()
    async def fetch_messages(
        self,
        limit: int = 50,
        since: Optional[datetime] = None,
        thread_id: Optional[str] = None,
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from Microsoft Teams.
        
        Args:
            limit: Maximum number of messages
            since: Only fetch messages after this timestamp
            thread_id: Optional chat/thread ID
        """
        if not self._connected or not self._graph_client:
            logger.error("Teams connector not connected")
            return []
        
        try:
            # Microsoft Graph API endpoint for Teams messages
            # This is a simplified example - real implementation would handle:
            # - Different chat types (1:1, group, channel)
            # - Pagination
            # - Filtering by date
            
            endpoint = "/chats"
            if thread_id:
                endpoint = f"/chats/{thread_id}/messages"
            else:
                # Get all chats and their messages
                endpoint = "/chats"
            
            # Stub implementation - would use actual Graph API calls
            logger.warning("Teams fetch_messages is a stub - implement with actual Graph API")
            
            # Example: Convert Teams message to UnifiedMessage
            # messages = await self._graph_client.get(endpoint)
            # return [self._convert_teams_message(msg) for msg in messages]
            
            return []
        except Exception as e:
            logger.error(f"Error fetching Teams messages: {e}")
            return []
    
    @with_error_boundary("Failed to send Teams message")
    @with_logging()
    async def send_message(
        self,
        content: str,
        to_user_id: str,
        thread_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> UnifiedMessage:
        """
        Send a message via Microsoft Teams.
        
        Args:
            content: Message text
            to_user_id: Recipient user ID or chat ID
            thread_id: Optional chat/thread ID
            attachments: Optional attachments
        """
        if not self._connected or not self._graph_client:
            raise RuntimeError("Teams connector not connected")
        
        try:
            # Microsoft Graph API format for sending Teams messages
            chat_id = thread_id or to_user_id
            
            payload = {
                "body": {
                    "contentType": "text",
                    "content": content,
                }
            }
            
            # Add attachments if provided
            if attachments:
                payload["attachments"] = attachments
            
            # Stub implementation
            logger.warning("Teams send_message is a stub - implement with actual Graph API")
            
            # Example:
            # response = await self._graph_client.post(f"/chats/{chat_id}/messages", json=payload)
            # return self._convert_teams_message(response)
            
            # Return stub UnifiedMessage
            return UnifiedMessage(
                id=f"teams_{datetime.utcnow().timestamp()}",
                source_type=SourceType.TEAMS,
                source_id="stub",
                thread_id=thread_id,
                content=content,
                from_user={"id": "current_user", "name": "Current User"},
                to_users=[{"id": to_user_id}],
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Failed to send Teams message: {e}")
            raise
    
    async def subscribe_to_events(
        self,
        callback: Callable[[UnifiedMessage], None],
    ) -> None:
        """
        Subscribe to real-time Teams message events.
        
        In a real implementation, this would set up Microsoft Graph webhooks
        or use change notifications.
        """
        self._event_callbacks.append(callback)
        logger.info(f"Subscribed callback to Teams events (total callbacks: {len(self._event_callbacks)})")
        
        # Stub: In real implementation, set up Graph webhooks
        logger.warning("Teams event subscription is a stub - implement Graph webhooks")
    
    def get_capabilities(self) -> ConnectorCapabilities:
        """Get Teams connector capabilities."""
        return ConnectorCapabilities(
            can_send=True,
            can_receive=True,
            can_search=True,
            can_archive=True,
            can_delete=True,
            supports_attachments=True,
            supports_reactions=True,
            supports_threading=True,
            supports_read_receipts=True,
        )
    
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self._connected
    
    def _convert_teams_message(self, teams_msg: Dict[str, Any]) -> UnifiedMessage:
        """
        Convert Teams message format to UnifiedMessage.
        
        This is a helper method to normalize Teams-specific data.
        """
        # This would contain the actual conversion logic
        # Example structure:
        return UnifiedMessage(
            id=f"teams_{teams_msg.get('id', 'unknown')}",
            source_type=SourceType.TEAMS,
            source_id=teams_msg.get('id', 'unknown'),
            thread_id=teams_msg.get('chatId'),
            content=teams_msg.get('body', {}).get('content', ''),
            from_user={
                "id": teams_msg.get('from', {}).get('user', {}).get('id'),
                "name": teams_msg.get('from', {}).get('user', {}).get('displayName'),
            },
            timestamp=datetime.fromisoformat(teams_msg.get('createdDateTime', datetime.utcnow().isoformat())),
            raw_data=teams_msg,
        )

