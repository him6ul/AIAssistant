"""
Assistant Orchestrator - Central coordinator for all connector operations.

The orchestrator aggregates data from all connectors, normalizes it,
stores it locally, and provides unified access methods.
"""

import asyncio
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime
from app.connectors.registry import get_registry
from app.connectors.services import (
    UnifiedMessageService,
    UnifiedInboxService,
    UnifiedNotesService,
)
from app.connectors.models import (
    UnifiedMessage,
    UnifiedEmail,
    UnifiedNote,
    SourceType,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AssistantOrchestrator:
    """
    Central orchestrator for the AI assistant.
    
    This class coordinates all connectors and provides:
    - Aggregated access to messages, emails, and notes
    - Local storage/caching
    - Search across all sources
    - Event notifications
    - Action recommendations
    """
    
    def __init__(self, registry=None):
        """
        Initialize assistant orchestrator.
        
        Args:
            registry: ConnectorRegistry instance (uses global if None)
        """
        self.registry = registry or get_registry()
        self.message_service = UnifiedMessageService(registry=self.registry)
        self.inbox_service = UnifiedInboxService(registry=self.registry)
        self.notes_service = UnifiedNotesService(registry=self.registry)
        
        # Local storage (in-memory for now, can be extended to SQLite/JSON)
        self._message_cache: List[UnifiedMessage] = []
        self._email_cache: List[UnifiedEmail] = []
        self._note_cache: List[UnifiedNote] = []
        
        # Event callbacks
        self._event_callbacks: List[Callable[[str, Any], None]] = []
    
    async def initialize(self) -> bool:
        """
        Initialize all registered connectors.
        
        Returns:
            True if initialization successful
        """
        logger.info("Initializing assistant orchestrator...")
        
        all_connectors = []
        message_connectors = self.registry.get_all_message_connectors()
        mail_connectors = self.registry.get_all_mail_connectors()
        note_connectors = self.registry.get_all_note_connectors()
        
        logger.info(f"Found {len(message_connectors)} message connector(s), {len(mail_connectors)} mail connector(s), {len(note_connectors)} note connector(s)")
        
        all_connectors.extend(message_connectors.values())
        all_connectors.extend(mail_connectors.values())
        all_connectors.extend(note_connectors.values())
        
        if not all_connectors:
            logger.warning("No connectors found in registry - initialization may have been called before connectors were registered")
            return False
        
        logger.info(f"Attempting to connect {len(all_connectors)} connector(s)...")
        success_count = 0
        for connector in all_connectors:
            try:
                connector_type = connector.source_type
                logger.info(f"Connecting {connector_type} connector...")
                
                # Check if already connected
                if hasattr(connector, '_connected') and connector._connected:
                    logger.info(f"{connector_type} connector already connected, skipping")
                    success_count += 1
                    continue
                
                # Connect with timeout
                import asyncio
                try:
                    connected = await asyncio.wait_for(connector.connect(), timeout=30.0)
                    if connected:
                        success_count += 1
                        logger.info(f"✅ Connected {connector_type} connector")
                    else:
                        logger.warning(f"⚠️  Failed to connect {connector_type} connector (returned False)")
                except asyncio.TimeoutError:
                    logger.error(f"❌ Timeout connecting {connector_type} connector (30s)")
                except Exception as e:
                    logger.error(f"❌ Error connecting {connector_type} connector: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"❌ Unexpected error processing connector: {e}", exc_info=True)
        
        logger.info(f"Initialized {success_count}/{len(all_connectors)} connector(s)")
        return success_count > 0
    
    async def shutdown(self) -> None:
        """Shutdown all connectors."""
        logger.info("Shutting down assistant orchestrator...")
        
        all_connectors = []
        all_connectors.extend(self.registry.get_all_message_connectors().values())
        all_connectors.extend(self.registry.get_all_mail_connectors().values())
        all_connectors.extend(self.registry.get_all_note_connectors().values())
        
        for connector in all_connectors:
            try:
                await connector.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting {connector.source_type}: {e}")
        
        logger.info("Assistant orchestrator shut down")
    
    async def refresh_all(self) -> Dict[str, int]:
        """
        Refresh data from all connectors and update local cache.
        
        Returns:
            Dictionary with counts of fetched items
        """
        logger.info("Refreshing data from all connectors...")
        
        counts = {
            "messages": 0,
            "emails": 0,
            "notes": 0,
        }
        
        try:
            # Fetch messages
            messages = await self.message_service.get_all_messages(limit=100)
            self._message_cache = messages
            counts["messages"] = len(messages)
            
            # Fetch emails
            emails = await self.inbox_service.get_all_emails(limit=100)
            self._email_cache = emails
            counts["emails"] = len(emails)
            
            # Fetch notes
            notes = await self.notes_service.get_all_notes(limit=100)
            self._note_cache = notes
            counts["notes"] = len(notes)
            
            logger.info(f"Refreshed: {counts['messages']} messages, {counts['emails']} emails, {counts['notes']} notes")
        except Exception as e:
            logger.error(f"Error refreshing data: {e}", exc_info=True)
        
        return counts
    
    async def get_all_messages(
        self,
        source_types: Optional[List[SourceType]] = None,
        limit: int = 50,
    ) -> List[UnifiedMessage]:
        """
        Get all messages from all connectors.
        
        Args:
            source_types: Optional list of source types to filter by
            limit: Maximum number of messages
        
        Returns:
            List of UnifiedMessage objects
        """
        return await self.message_service.get_all_messages(
            limit=limit,
            source_types=source_types,
        )
    
    async def get_all_emails(
        self,
        source_types: Optional[List[SourceType]] = None,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[UnifiedEmail]:
        """
        Get all emails from all connectors.
        
        Args:
            source_types: Optional list of source types to filter by
            unread_only: Only fetch unread emails
            limit: Maximum number of emails
        
        Returns:
            List of UnifiedEmail objects
        """
        return await self.inbox_service.get_all_emails(
            limit=limit,
            source_types=source_types,
            unread_only=unread_only,
        )
    
    async def get_all_notes(
        self,
        source_types: Optional[List[SourceType]] = None,
        limit: int = 50,
    ) -> List[UnifiedNote]:
        """
        Get all notes from all connectors.
        
        Args:
            source_types: Optional list of source types to filter by
            limit: Maximum number of notes
        
        Returns:
            List of UnifiedNote objects
        """
        return await self.notes_service.get_all_notes(
            limit=limit,
            source_types=source_types,
        )
    
    async def search_across_sources(
        self,
        query: str,
        source_types: Optional[List[SourceType]] = None,
        limit: int = 50,
    ) -> Dict[str, List[Any]]:
        """
        Search across all sources (messages, emails, notes).
        
        Args:
            query: Search query string
            source_types: Optional list of source types to search
            limit: Maximum number of results per type
        
        Returns:
            Dictionary with 'messages', 'emails', and 'notes' keys
        """
        logger.info(f"Searching across all sources for: {query}")
        
        results = {
            "messages": [],
            "emails": [],
            "notes": [],
        }
        
        try:
            # Search messages
            messages = await self.message_service.search_messages(
                query=query,
                source_types=source_types,
                limit=limit,
            )
            results["messages"] = messages
            
            # Search emails
            emails = await self.inbox_service.search_emails(
                query=query,
                source_types=source_types,
                limit=limit,
            )
            results["emails"] = emails
            
            # Search notes (simple text search)
            notes = await self.notes_service.get_all_notes(
                limit=limit * 2,
                source_types=source_types,
            )
            query_lower = query.lower()
            matching_notes = [
                note for note in notes
                if query_lower in note.title.lower() or
                   query_lower in note.content.lower()
            ]
            results["notes"] = matching_notes[:limit]
            
            logger.info(f"Search results: {len(results['messages'])} messages, "
                       f"{len(results['emails'])} emails, {len(results['notes'])} notes")
        except Exception as e:
            logger.error(f"Error searching across sources: {e}", exc_info=True)
        
        return results
    
    async def get_next_actions(self) -> List[Dict[str, Any]]:
        """
        Get recommended next actions based on current data.
        
        This analyzes messages, emails, and notes to suggest actions like:
        - Reply to unread messages
        - Respond to important emails
        - Review meeting reminders
        - etc.
        
        Returns:
            List of action recommendations
        """
        actions = []
        
        try:
            # Get unread emails
            unread_emails = await self.get_all_emails(unread_only=True, limit=10)
            for email in unread_emails[:5]:  # Top 5
                if email.is_important or email.priority.value == "high":
                    actions.append({
                        "type": "reply_email",
                        "priority": "high",
                        "description": f"Reply to important email: {email.subject}",
                        "source_type": email.source_type,
                        "source_id": email.id,
                        "data": email,
                    })
            
            # Get recent messages
            recent_messages = await self.get_all_messages(limit=10)
            unread_messages = [m for m in recent_messages if not m.is_read][:5]
            for message in unread_messages:
                actions.append({
                    "type": "reply_message",
                    "priority": "medium",
                    "description": f"Reply to message from {message.from_user.get('name', 'Unknown')}",
                    "source_type": message.source_type,
                    "source_id": message.id,
                    "data": message,
                })
            
            # Sort by priority
            priority_order = {"high": 0, "medium": 1, "low": 2}
            actions.sort(key=lambda a: priority_order.get(a.get("priority", "low"), 2))
            
        except Exception as e:
            logger.error(f"Error getting next actions: {e}", exc_info=True)
        
        return actions
    
    def subscribe_to_events(
        self,
        callback: Callable[[str, Any], None],
    ) -> None:
        """
        Subscribe to events from all connectors.
        
        Args:
            callback: Function to call when event occurs
                     Signature: callback(event_type: str, data: Any)
        """
        self._event_callbacks.append(callback)
        logger.info(f"Subscribed to orchestrator events (total callbacks: {len(self._event_callbacks)})")
    
    def _notify_event(self, event_type: str, data: Any) -> None:
        """Notify all event subscribers."""
        for callback in self._event_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

