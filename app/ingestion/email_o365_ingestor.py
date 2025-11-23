"""
Office 365 email ingestion via Microsoft Graph API.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.ingestion.ms_graph_client import get_graph_client
from app.tasks.storage import get_task_storage
from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmailO365Ingestor:
    """
    Ingests emails from Office 365 via Microsoft Graph API.
    """
    
    def __init__(self, action_keywords: List[str] = None):
        """
        Initialize email ingestor.
        
        Args:
            action_keywords: Keywords that indicate actionable emails
        """
        self.graph_client = get_graph_client()
        if self.graph_client is None:
            raise ValueError("Microsoft Graph client not available. Please configure MS_CLIENT_ID, MS_CLIENT_SECRET, and MS_TENANT_ID environment variables.")
        self.storage = get_task_storage()
        self.action_keywords = action_keywords or [
            "follow up", "due", "please check", "action required", "todo", "task"
        ]
        self._processed_emails: set = set()
    
    def _contains_action_keywords(self, subject: str, body: str) -> bool:
        """
        Check if email contains action keywords.
        
        Args:
            subject: Email subject
            body: Email body
        
        Returns:
            True if contains action keywords
        """
        text = f"{subject} {body}".lower()
        return any(keyword.lower() in text for keyword in self.action_keywords)
    
    async def get_messages(
        self,
        folder: str = "Inbox",
        filter_query: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get email messages from a folder.
        
        Args:
            folder: Folder name (Inbox, SentItems, etc.)
            filter_query: OData filter query
            max_results: Maximum number of results
        
        Returns:
            List of message objects
        """
        try:
            # Use /users/{userPrincipalName} endpoint for app-only authentication
            # Fall back to /me if user principal not available (for delegated auth)
            user_principal = os.getenv("MS_USER_PRINCIPAL_NAME")
            
            if user_principal:
                # App-only authentication - use /users/{userPrincipalName}
                endpoint = f"/users/{user_principal}/mailFolders/{folder}/messages"
                logger.debug(f"Using app-only auth endpoint: {endpoint}")
            else:
                # Delegated authentication - use /me
                endpoint = f"/me/mailFolders/{folder}/messages"
                logger.debug(f"Using delegated auth endpoint: {endpoint}")
            
            params = {
                "$top": max_results,
                "$select": "id,subject,bodyPreview,body,from,receivedDateTime,isRead,flag,importance"
            }
            
            if filter_query:
                params["$filter"] = filter_query
            
            response = await self.graph_client.make_request("GET", endpoint, params=params)
            messages = response.get("value", [])
            logger.info(f"Found {len(messages)} messages in {folder}")
            return messages
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []
    
    async def get_message_content(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full content of a message.
        
        Args:
            message_id: Message ID
        
        Returns:
            Message content dict
        """
        try:
            # Use /users/{userPrincipalName} endpoint for app-only authentication
            user_principal = os.getenv("MS_USER_PRINCIPAL_NAME")
            
            if user_principal:
                # App-only authentication
                endpoint = f"/users/{user_principal}/messages/{message_id}"
                logger.debug(f"Using app-only auth endpoint: {endpoint}")
            else:
                # Delegated authentication
                endpoint = f"/me/messages/{message_id}"
                logger.debug(f"Using delegated auth endpoint: {endpoint}")
            
            response = await self.graph_client.make_request(
                "GET",
                endpoint,
                params={
                    "$select": "id,subject,body,bodyPreview,from,receivedDateTime,isRead,flag,importance,toRecipients,ccRecipients"
                }
            )
            return response
        except Exception as e:
            logger.error(f"Failed to get message content: {e}")
            return None
    
    def _extract_text_from_body(self, body: Dict[str, Any]) -> str:
        """
        Extract text from email body (HTML or text).
        
        Args:
            body: Body object with content and contentType
        
        Returns:
            Plain text content
        """
        if not body:
            return ""
        
        content = body.get("content", "")
        content_type = body.get("contentType", "text")
        
        if content_type == "html":
            # Simple HTML to text conversion
            from bs4 import BeautifulSoup
            try:
                soup = BeautifulSoup(content, 'html.parser')
                return soup.get_text()
            except:
                return content
        else:
            return content
    
    async def ingest_unread(self, max_emails: int = 50) -> List[Dict[str, Any]]:
        """
        Ingest unread emails.
        
        Args:
            max_emails: Maximum number of emails to ingest
        
        Returns:
            List of ingested email data
        """
        logger.info("Starting unread email ingestion")
        
        messages = await self.get_messages(
            folder="Inbox",
            filter_query="isRead eq false",
            max_results=max_emails
        )
        
        ingested_emails = []
        for message in messages:
            message_id = message.get("id")
            
            # Skip if already processed
            if message_id in self._processed_emails:
                continue
            
            # Get full message content
            full_message = await self.get_message_content(message_id)
            if not full_message:
                continue
            
            # Extract text
            body_text = self._extract_text_from_body(full_message.get("body"))
            subject = full_message.get("subject", "")
            
            # Check for action keywords
            if self._contains_action_keywords(subject, body_text):
                ingested_emails.append({
                    "id": message_id,
                    "subject": subject,
                    "body": body_text,
                    "from": full_message.get("from", {}).get("emailAddress", {}).get("address", ""),
                    "received": full_message.get("receivedDateTime"),
                    "importance": full_message.get("importance", "normal"),
                    "is_read": full_message.get("isRead", False)
                })
                
                self._processed_emails.add(message_id)
                
                # Log ingestion
                await self.storage.log_ingestion(
                    source_type="email",
                    source_id=message_id,
                    status="success"
                )
        
        logger.info(f"Ingested {len(ingested_emails)} unread emails")
        return ingested_emails
    
    async def ingest_flagged(self, max_emails: int = 50) -> List[Dict[str, Any]]:
        """
        Ingest flagged emails.
        
        Args:
            max_emails: Maximum number of emails to ingest
        
        Returns:
            List of ingested email data
        """
        logger.info("Starting flagged email ingestion")
        
        messages = await self.get_messages(
            folder="Inbox",
            filter_query="flag/flagStatus eq 'flagged'",
            max_results=max_emails
        )
        
        ingested_emails = []
        for message in messages:
            message_id = message.get("id")
            
            if message_id in self._processed_emails:
                continue
            
            full_message = await self.get_message_content(message_id)
            if not full_message:
                continue
            
            body_text = self._extract_text_from_body(full_message.get("body"))
            subject = full_message.get("subject", "")
            
            ingested_emails.append({
                "id": message_id,
                "subject": subject,
                "body": body_text,
                "from": full_message.get("from", {}).get("emailAddress", {}).get("address", ""),
                "received": full_message.get("receivedDateTime"),
                "importance": full_message.get("importance", "normal"),
                "is_read": full_message.get("isRead", False)
            })
            
            self._processed_emails.add(message_id)
            
            await self.storage.log_ingestion(
                source_type="email",
                source_id=message_id,
                status="success"
            )
        
        logger.info(f"Ingested {len(ingested_emails)} flagged emails")
        return ingested_emails
    
    async def ingest_recent(self, days: int = 7, max_emails: int = 50) -> List[Dict[str, Any]]:
        """
        Ingest recent emails.
        
        Args:
            days: Number of days to look back
            max_emails: Maximum number of emails to ingest
        
        Returns:
            List of ingested email data
        """
        logger.info(f"Starting recent email ingestion (last {days} days)")
        
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        filter_query = f"receivedDateTime ge {cutoff_date}"
        
        messages = await self.get_messages(
            folder="Inbox",
            filter_query=filter_query,
            max_results=max_emails
        )
        
        ingested_emails = []
        for message in messages:
            message_id = message.get("id")
            
            if message_id in self._processed_emails:
                continue
            
            # Only ingest if contains action keywords
            subject = message.get("subject", "")
            body_preview = message.get("bodyPreview", "")
            
            if self._contains_action_keywords(subject, body_preview):
                full_message = await self.get_message_content(message_id)
                if not full_message:
                    continue
                
                body_text = self._extract_text_from_body(full_message.get("body"))
                
                ingested_emails.append({
                    "id": message_id,
                    "subject": subject,
                    "body": body_text,
                    "from": full_message.get("from", {}).get("emailAddress", {}).get("address", ""),
                    "received": full_message.get("receivedDateTime"),
                    "importance": full_message.get("importance", "normal"),
                    "is_read": full_message.get("isRead", False)
                })
                
                self._processed_emails.add(message_id)
                
                await self.storage.log_ingestion(
                    source_type="email",
                    source_id=message_id,
                    status="success"
                )
        
        logger.info(f"Ingested {len(ingested_emails)} recent emails")
        return ingested_emails

