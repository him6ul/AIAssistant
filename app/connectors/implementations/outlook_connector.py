"""
Microsoft Outlook connector implementation using Microsoft Graph API.
"""

import os
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
from app.connectors.base import MailSourceConnector, ConnectorCapabilities
from app.connectors.models import UnifiedEmail, SourceType
from app.connectors.middleware import with_retry, RetryConfig, with_error_boundary, with_logging
from app.ingestion.ms_graph_client import MSGraphClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OutlookConnector(MailSourceConnector):
    """
    Microsoft Outlook connector using Microsoft Graph API.
    
    This connector implements the MailSourceConnector interface
    and converts Outlook-specific data to UnifiedEmail format.
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize Outlook connector.
        
        Args:
            client_id: Microsoft Azure AD client ID
            client_secret: Microsoft Azure AD client secret
            tenant_id: Microsoft Azure AD tenant ID
        """
        self.client_id = client_id or os.getenv("MS_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("MS_CLIENT_SECRET")
        self.tenant_id = tenant_id or os.getenv("MS_TENANT_ID")
        self._graph_client: Optional[MSGraphClient] = None
        self._connected = False
        self._event_callbacks: List[Callable[[UnifiedEmail], None]] = []
        
        self._retry_config = RetryConfig(max_retries=3, initial_delay=1.0)
    
    @property
    def source_type(self) -> SourceType:
        """Return Outlook source type."""
        return SourceType.OUTLOOK
    
    @with_logging()
    @with_retry(RetryConfig(max_retries=3))
    async def connect(self) -> bool:
        """Connect to Microsoft Graph API."""
        try:
            if not all([self.client_id, self.client_secret, self.tenant_id]):
                logger.error("Outlook credentials not configured")
                return False
            
            self._graph_client = MSGraphClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                tenant_id=self.tenant_id,
            )
            
            # Test connection
            await self._graph_client.get_access_token()
            self._connected = True
            logger.info("Outlook connector connected successfully")
            return True
        except Exception as e:
            logger.error(f"Error connecting to Outlook: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Microsoft Graph API."""
        self._graph_client = None
        self._connected = False
        logger.info("Outlook connector disconnected")
    
    @with_error_boundary("Failed to fetch Outlook emails", return_on_error=[])
    @with_logging()
    async def fetch_emails(
        self,
        limit: int = 50,
        folder: Optional[str] = None,
        unread_only: bool = False,
        since: Optional[datetime] = None,
    ) -> List[UnifiedEmail]:
        """
        Fetch emails from Outlook.
        
        Args:
            limit: Maximum number of emails
            folder: Folder name (inbox, sent, etc.)
            unread_only: Only fetch unread emails
            since: Only fetch emails after this timestamp
        """
        if not self._connected or not self._graph_client:
            logger.error("Outlook connector not connected")
            return []
        
        try:
            # Build Microsoft Graph API query
            folder_path = folder or "inbox"
            endpoint = f"/me/mailFolders/{folder_path}/messages"
            
            # Build filter query
            filters = []
            if unread_only:
                filters.append("isRead eq false")
            if since:
                filters.append(f"receivedDateTime ge {since.isoformat()}Z")
            
            query_params = {
                "$top": limit,
                "$orderby": "receivedDateTime desc",
            }
            if filters:
                query_params["$filter"] = " and ".join(filters)
            
            # Use existing email ingestor logic if available
            # For now, stub implementation
            logger.warning("Outlook fetch_emails is a stub - implement with actual Graph API")
            
            # Example:
            # response = await self._graph_client.get(endpoint, params=query_params)
            # emails = response.get('value', [])
            # return [self._convert_outlook_email(email) for email in emails]
            
            return []
        except Exception as e:
            logger.error(f"Error fetching Outlook emails: {e}")
            return []
    
    @with_error_boundary("Failed to send Outlook email")
    @with_logging()
    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        cc_addresses: Optional[List[str]] = None,
        bcc_addresses: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> UnifiedEmail:
        """
        Send an email via Outlook.
        
        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: Optional HTML body
            cc_addresses: Optional CC addresses
            bcc_addresses: Optional BCC addresses
            attachments: Optional attachments
        """
        if not self._connected or not self._graph_client:
            raise RuntimeError("Outlook connector not connected")
        
        try:
            # Microsoft Graph API format for sending emails
            payload = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "html" if body_html else "text",
                        "content": body_html or body_text,
                    },
                    "toRecipients": [{"emailAddress": {"address": addr}} for addr in to_addresses],
                },
                "saveToSentItems": True,
            }
            
            if cc_addresses:
                payload["message"]["ccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in cc_addresses
                ]
            
            if bcc_addresses:
                payload["message"]["bccRecipients"] = [
                    {"emailAddress": {"address": addr}} for addr in bcc_addresses
                ]
            
            if attachments:
                payload["message"]["attachments"] = attachments
            
            # Stub implementation
            logger.warning("Outlook send_email is a stub - implement with actual Graph API")
            
            # Example:
            # response = await self._graph_client.post("/me/sendMail", json=payload)
            # return self._convert_outlook_email(response)
            
            # Return stub UnifiedEmail
            return UnifiedEmail(
                id=f"outlook_{datetime.utcnow().timestamp()}",
                source_type=SourceType.OUTLOOK,
                source_id="stub",
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                from_address={"email": "current_user@outlook.com", "name": "Current User"},
                to_addresses=[{"email": addr} for addr in to_addresses],
                cc_addresses=[{"email": addr} for addr in (cc_addresses or [])],
                bcc_addresses=[{"email": addr} for addr in (bcc_addresses or [])],
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Failed to send Outlook email: {e}")
            raise
    
    @with_error_boundary("Failed to search Outlook emails", return_on_error=[])
    @with_logging()
    async def search_emails(
        self,
        query: str,
        limit: int = 50,
    ) -> List[UnifiedEmail]:
        """
        Search emails using Microsoft Graph search.
        
        Args:
            query: Search query string
            limit: Maximum number of results
        """
        if not self._connected or not self._graph_client:
            logger.error("Outlook connector not connected")
            return []
        
        try:
            # Microsoft Graph search endpoint
            endpoint = "/me/messages"
            query_params = {
                "$search": f'"{query}"',
                "$top": limit,
            }
            
            # Stub implementation
            logger.warning("Outlook search_emails is a stub - implement with actual Graph API")
            
            # Example:
            # response = await self._graph_client.get(endpoint, params=query_params)
            # emails = response.get('value', [])
            # return [self._convert_outlook_email(email) for email in emails]
            
            return []
        except Exception as e:
            logger.error(f"Error searching Outlook emails: {e}")
            return []
    
    @with_error_boundary("Failed to get Outlook folders", return_on_error=[])
    @with_logging()
    async def get_mailbox_folders(self) -> List[Dict[str, Any]]:
        """Get list of Outlook mailbox folders."""
        if not self._connected or not self._graph_client:
            logger.error("Outlook connector not connected")
            return []
        
        try:
            endpoint = "/me/mailFolders"
            # Stub implementation
            logger.warning("Outlook get_mailbox_folders is a stub - implement with actual Graph API")
            
            # Example:
            # response = await self._graph_client.get(endpoint)
            # return response.get('value', [])
            
            return [
                {"id": "inbox", "name": "Inbox"},
                {"id": "sent", "name": "Sent Items"},
                {"id": "drafts", "name": "Drafts"},
            ]
        except Exception as e:
            logger.error(f"Error getting Outlook folders: {e}")
            return []
    
    async def subscribe_to_new_mail(
        self,
        callback: Callable[[UnifiedEmail], None],
    ) -> None:
        """
        Subscribe to new email notifications.
        
        In a real implementation, this would set up Microsoft Graph webhooks
        or use change notifications.
        """
        self._event_callbacks.append(callback)
        logger.info(f"Subscribed callback to Outlook new mail (total callbacks: {len(self._event_callbacks)})")
        
        # Stub: In real implementation, set up Graph webhooks
        logger.warning("Outlook new mail subscription is a stub - implement Graph webhooks")
    
    def get_capabilities(self) -> ConnectorCapabilities:
        """Get Outlook connector capabilities."""
        return ConnectorCapabilities(
            can_send=True,
            can_receive=True,
            can_search=True,
            can_archive=True,
            can_delete=True,
            supports_attachments=True,
            supports_reactions=False,
            supports_threading=True,
            supports_read_receipts=False,
        )
    
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self._connected
    
    def _convert_outlook_email(self, outlook_email: Dict[str, Any]) -> UnifiedEmail:
        """
        Convert Outlook email format to UnifiedEmail.
        
        This is a helper method to normalize Outlook-specific data.
        """
        # This would contain the actual conversion logic
        return UnifiedEmail(
            id=f"outlook_{outlook_email.get('id', 'unknown')}",
            source_type=SourceType.OUTLOOK,
            source_id=outlook_email.get('id', 'unknown'),
            subject=outlook_email.get('subject', ''),
            body_text=outlook_email.get('body', {}).get('content', ''),
            body_html=outlook_email.get('body', {}).get('content', '') if outlook_email.get('body', {}).get('contentType') == 'html' else None,
            from_address={
                "email": outlook_email.get('from', {}).get('emailAddress', {}).get('address'),
                "name": outlook_email.get('from', {}).get('emailAddress', {}).get('name'),
            },
            to_addresses=[
                {"email": addr.get('emailAddress', {}).get('address')}
                for addr in outlook_email.get('toRecipients', [])
            ],
            timestamp=datetime.fromisoformat(outlook_email.get('receivedDateTime', datetime.utcnow().isoformat())),
            is_read=outlook_email.get('isRead', False),
            folder=outlook_email.get('parentFolderId'),
            raw_data=outlook_email,
        )

