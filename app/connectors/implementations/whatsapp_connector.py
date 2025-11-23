"""
WhatsApp connector implementation using WhatsApp Cloud API.

This is a stub implementation that can be extended with actual
WhatsApp Cloud API integration.
"""

import os
import httpx
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
from app.connectors.base import MessageSourceConnector, ConnectorCapabilities
from app.connectors.models import UnifiedMessage, SourceType
from app.connectors.middleware import with_retry, RetryConfig, with_error_boundary, with_logging
from app.utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppConnector(MessageSourceConnector):
    """
    WhatsApp connector using WhatsApp Cloud API.
    
    This connector implements the MessageSourceConnector interface
    and converts WhatsApp-specific data to UnifiedMessage format.
    """
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        business_account_id: Optional[str] = None,
    ):
        """
        Initialize WhatsApp connector.
        
        Args:
            api_token: WhatsApp Cloud API token
            phone_number_id: WhatsApp Business phone number ID
            business_account_id: WhatsApp Business account ID
        """
        self.api_token = api_token or os.getenv("WHATSAPP_API_TOKEN")
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.business_account_id = business_account_id or os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
        self.base_url = "https://graph.facebook.com/v18.0"
        self._connected = False
        self._client: Optional[httpx.AsyncClient] = None
        self._event_callbacks: List[Callable[[UnifiedMessage], None]] = []
        
        # Retry config for API calls
        self._retry_config = RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            max_delay=10.0,
        )
    
    @property
    def source_type(self) -> SourceType:
        """Return WhatsApp source type."""
        return SourceType.WHATSAPP
    
    @with_logging()
    @with_retry(RetryConfig(max_retries=3))
    async def connect(self) -> bool:
        """Connect to WhatsApp Cloud API."""
        try:
            if not self.api_token or not self.phone_number_id:
                logger.error("WhatsApp credentials not configured")
                return False
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
            
            # Verify connection by checking phone number
            response = await self._client.get(f"/{self.phone_number_id}")
            if response.status_code == 200:
                self._connected = True
                logger.info("WhatsApp connector connected successfully")
                return True
            else:
                logger.error(f"Failed to connect to WhatsApp: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to WhatsApp: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from WhatsApp API."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("WhatsApp connector disconnected")
    
    @with_error_boundary("Failed to fetch WhatsApp messages", return_on_error=[])
    @with_logging()
    async def fetch_messages(
        self,
        limit: int = 50,
        since: Optional[datetime] = None,
        thread_id: Optional[str] = None,
    ) -> List[UnifiedMessage]:
        """
        Fetch messages from WhatsApp.
        
        Note: This is a stub implementation. Real implementation would
        use WhatsApp Cloud API webhooks or polling.
        """
        # Stub implementation - in real scenario, this would:
        # 1. Poll WhatsApp API for new messages
        # 2. Or receive webhooks from WhatsApp
        # 3. Convert WhatsApp message format to UnifiedMessage
        
        logger.warning("WhatsApp fetch_messages is a stub - implement with actual API")
        
        # Example stub response
        return []
    
    @with_error_boundary("Failed to send WhatsApp message")
    @with_logging()
    async def send_message(
        self,
        content: str,
        to_user_id: str,
        thread_id: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> UnifiedMessage:
        """
        Send a message via WhatsApp.
        
        Args:
            content: Message text
            to_user_id: Recipient WhatsApp number (with country code, e.g., "14155551234")
            thread_id: Optional conversation/thread ID
            attachments: Optional attachments (images, documents, etc.)
        """
        if not self._connected or not self._client:
            raise RuntimeError("WhatsApp connector not connected")
        
        # WhatsApp Cloud API message format
        payload = {
            "messaging_product": "whatsapp",
            "to": to_user_id,
            "type": "text",
            "text": {"body": content},
        }
        
        # Add attachments if provided
        if attachments:
            # Convert attachments to WhatsApp format
            # (This is simplified - real implementation would handle different attachment types)
            logger.warning("Attachments not fully implemented in stub")
        
        try:
            response = await self._client.post(
                f"/{self.phone_number_id}/messages",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            # Convert WhatsApp response to UnifiedMessage
            return UnifiedMessage(
                id=f"whatsapp_{data.get('messages', [{}])[0].get('id', 'unknown')}",
                source_type=SourceType.WHATSAPP,
                source_id=data.get('messages', [{}])[0].get('id', 'unknown'),
                thread_id=thread_id,
                content=content,
                from_user={
                    "id": self.phone_number_id,
                    "name": "WhatsApp Business",
                },
                to_users=[{"id": to_user_id, "phone": to_user_id}],
                timestamp=datetime.utcnow(),
                raw_data=data,
            )
        except httpx.HTTPError as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            raise
    
    async def subscribe_to_events(
        self,
        callback: Callable[[UnifiedMessage], None],
    ) -> None:
        """
        Subscribe to real-time WhatsApp message events.
        
        In a real implementation, this would set up webhook handlers
        or polling mechanisms to receive new messages.
        """
        self._event_callbacks.append(callback)
        logger.info(f"Subscribed callback to WhatsApp events (total callbacks: {len(self._event_callbacks)})")
        
        # Stub: In real implementation, start webhook server or polling
        logger.warning("WhatsApp event subscription is a stub - implement webhook handler")
    
    def get_capabilities(self) -> ConnectorCapabilities:
        """Get WhatsApp connector capabilities."""
        return ConnectorCapabilities(
            can_send=True,
            can_receive=True,
            can_search=False,  # WhatsApp Cloud API has limited search
            can_archive=False,
            can_delete=False,
            supports_attachments=True,
            supports_reactions=False,
            supports_threading=True,
            supports_read_receipts=True,
        )
    
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self._connected

