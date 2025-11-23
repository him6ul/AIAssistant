"""
Microsoft OneNote connector implementation using Microsoft Graph API.
"""

import os
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.connectors.base import NoteSourceConnector, ConnectorCapabilities
from app.connectors.models import UnifiedNote, SourceType
from app.connectors.middleware import with_retry, RetryConfig, with_error_boundary, with_logging
from app.ingestion.ms_graph_client import MSGraphClient
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OneNoteConnector(NoteSourceConnector):
    """
    Microsoft OneNote connector using Microsoft Graph API.
    
    This connector implements the NoteSourceConnector interface
    and converts OneNote-specific data to UnifiedNote format.
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ):
        """
        Initialize OneNote connector.
        
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
        
        self._retry_config = RetryConfig(max_retries=3, initial_delay=1.0)
    
    @property
    def source_type(self) -> SourceType:
        """Return OneNote source type."""
        return SourceType.ONENOTE
    
    @with_logging()
    @with_retry(RetryConfig(max_retries=3))
    async def connect(self) -> bool:
        """Connect to Microsoft Graph API."""
        try:
            if not all([self.client_id, self.client_secret, self.tenant_id]):
                logger.error("OneNote credentials not configured")
                return False
            
            self._graph_client = MSGraphClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                tenant_id=self.tenant_id,
            )
            
            # Test connection
            await self._graph_client.get_access_token()
            self._connected = True
            logger.info("OneNote connector connected successfully")
            return True
        except Exception as e:
            logger.error(f"Error connecting to OneNote: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Microsoft Graph API."""
        self._graph_client = None
        self._connected = False
        logger.info("OneNote connector disconnected")
    
    @with_error_boundary("Failed to fetch OneNote notes", return_on_error=[])
    @with_logging()
    async def fetch_notes(
        self,
        limit: int = 50,
        notebook_id: Optional[str] = None,
        section_id: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[UnifiedNote]:
        """
        Fetch notes from OneNote.
        
        Args:
            limit: Maximum number of notes
            notebook_id: Optional notebook ID to filter by
            section_id: Optional section ID to filter by
            since: Only fetch notes updated after this timestamp
        """
        if not self._connected or not self._graph_client:
            logger.error("OneNote connector not connected")
            return []
        
        try:
            # Build Microsoft Graph API endpoint
            if section_id:
                endpoint = f"/me/onenote/sections/{section_id}/pages"
            elif notebook_id:
                endpoint = f"/me/onenote/notebooks/{notebook_id}/sections"
                # Would need to get pages from sections
            else:
                endpoint = "/me/onenote/pages"
            
            # Build query parameters
            query_params = {"$top": limit}
            if since:
                query_params["$filter"] = f"lastModifiedDateTime ge {since.isoformat()}Z"
            
            # Use existing OneNote ingestor logic if available
            # For now, stub implementation
            logger.warning("OneNote fetch_notes is a stub - implement with actual Graph API")
            
            # Example:
            # response = await self._graph_client.get(endpoint, params=query_params)
            # pages = response.get('value', [])
            # return [self._convert_onenote_page(page) for page in pages]
            
            return []
        except Exception as e:
            logger.error(f"Error fetching OneNote notes: {e}")
            return []
    
    @with_error_boundary("Failed to create OneNote note")
    @with_logging()
    async def create_note(
        self,
        title: str,
        content: str,
        notebook_id: Optional[str] = None,
        section_id: Optional[str] = None,
        content_html: Optional[str] = None,
    ) -> UnifiedNote:
        """
        Create a new OneNote page.
        
        Args:
            title: Note title
            content: Note content (plain text)
            notebook_id: Optional notebook ID
            section_id: Optional section ID (required if notebook_id not provided)
            content_html: Optional HTML content
        """
        if not self._connected or not self._graph_client:
            raise RuntimeError("OneNote connector not connected")
        
        if not section_id and not notebook_id:
            raise ValueError("Either section_id or notebook_id must be provided")
        
        try:
            # Microsoft Graph API format for creating OneNote pages
            # OneNote uses HTML format for page content
            html_content = content_html or f"<p>{content.replace(chr(10), '<br>')}</p>"
            
            # Create HTML document for OneNote
            onenote_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{title}</title>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            endpoint = f"/me/onenote/sections/{section_id}/pages"
            
            # Stub implementation
            logger.warning("OneNote create_note is a stub - implement with actual Graph API")
            
            # Example:
            # response = await self._graph_client.post(
            #     endpoint,
            #     data=onenote_html,
            #     headers={"Content-Type": "text/html"}
            # )
            # return self._convert_onenote_page(response)
            
            # Return stub UnifiedNote
            return UnifiedNote(
                id=f"onenote_{datetime.utcnow().timestamp()}",
                source_type=SourceType.ONENOTE,
                source_id="stub",
                title=title,
                content=content,
                content_html=content_html,
                section_id=section_id,
                notebook_id=notebook_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Failed to create OneNote note: {e}")
            raise
    
    @with_error_boundary("Failed to update OneNote note")
    @with_logging()
    async def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        content_html: Optional[str] = None,
    ) -> UnifiedNote:
        """
        Update an existing OneNote page.
        
        Args:
            note_id: ID of note (page) to update
            title: Optional new title
            content: Optional new content (plain text)
            content_html: Optional new HTML content
        """
        if not self._connected or not self._graph_client:
            raise RuntimeError("OneNote connector not connected")
        
        try:
            # Microsoft Graph API for updating OneNote pages
            # OneNote updates are done via PATCH with HTML content
            endpoint = f"/me/onenote/pages/{note_id}/content"
            
            # Stub implementation
            logger.warning("OneNote update_note is a stub - implement with actual Graph API")
            
            # Example:
            # if content_html:
            #     await self._graph_client.patch(endpoint, data=content_html, headers={"Content-Type": "text/html"})
            # response = await self._graph_client.get(f"/me/onenote/pages/{note_id}")
            # return self._convert_onenote_page(response)
            
            # Return stub UnifiedNote
            return UnifiedNote(
                id=f"onenote_{note_id}",
                source_type=SourceType.ONENOTE,
                source_id=note_id,
                title=title or "Updated Note",
                content=content or "",
                content_html=content_html,
                updated_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Failed to update OneNote note: {e}")
            raise
    
    def get_capabilities(self) -> ConnectorCapabilities:
        """Get OneNote connector capabilities."""
        return ConnectorCapabilities(
            can_send=False,  # Notes don't have "send" concept
            can_receive=True,
            can_search=True,
            can_archive=False,
            can_delete=False,  # Would need separate delete method
            supports_attachments=True,
            supports_reactions=False,
            supports_threading=False,
            supports_read_receipts=False,
        )
    
    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self._connected
    
    def _convert_onenote_page(self, onenote_page: Dict[str, Any]) -> UnifiedNote:
        """
        Convert OneNote page format to UnifiedNote.
        
        This is a helper method to normalize OneNote-specific data.
        """
        return UnifiedNote(
            id=f"onenote_{onenote_page.get('id', 'unknown')}",
            source_type=SourceType.ONENOTE,
            source_id=onenote_page.get('id', 'unknown'),
            title=onenote_page.get('title', ''),
            content=onenote_page.get('content', ''),  # Would need to extract text from HTML
            content_html=onenote_page.get('content', ''),
            notebook_id=onenote_page.get('parentNotebook', {}).get('id'),
            notebook_name=onenote_page.get('parentNotebook', {}).get('displayName'),
            section_id=onenote_page.get('parentSection', {}).get('id'),
            section_name=onenote_page.get('parentSection', {}).get('displayName'),
            page_id=onenote_page.get('id'),
            created_at=datetime.fromisoformat(onenote_page.get('createdDateTime', datetime.utcnow().isoformat())),
            updated_at=datetime.fromisoformat(onenote_page.get('lastModifiedDateTime', datetime.utcnow().isoformat())),
            raw_data=onenote_page,
        )

