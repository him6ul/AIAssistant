"""
Example usage of the connector architecture.

This demonstrates how to:
1. Initialize connectors
2. Register them in the registry
3. Use the orchestrator
4. Access unified data
"""

import asyncio
import os
from dotenv import load_dotenv
from app.connectors.registry import get_registry
from app.connectors.orchestrator import AssistantOrchestrator
from app.connectors.models import SourceType
from app.connectors.implementations import (
    OutlookConnector,
    GmailConnector,
)

# Load environment variables
load_dotenv()


async def main():
    """Main example function."""
    print("🚀 Initializing AI Assistant with Connector Architecture\n")
    
    # Get the registry
    registry = get_registry()
    
    # Initialize connectors based on configuration
    # In a real application, this would be driven by config file
    connectors_config = {
        "outlook": os.getenv("ENABLE_OUTLOOK", "false").lower() == "true",
        "gmail": os.getenv("ENABLE_GMAIL", "false").lower() == "true",
    }
    
    # Register connectors
    if connectors_config["outlook"]:
        outlook = OutlookConnector()
        registry.register_mail_connector(SourceType.OUTLOOK, outlook)
        print("✅ Registered Outlook connector")
    
    if connectors_config["gmail"]:
        gmail = GmailConnector()
        registry.register_mail_connector(SourceType.GMAIL, gmail)
        print("✅ Registered Gmail connector")
    
    print(f"\n📋 Registered {len(registry.get_registered_types())} connector(s)\n")
    
    # Initialize orchestrator
    orchestrator = AssistantOrchestrator(registry=registry)
    
    # Initialize all connectors
    print("🔌 Connecting to all registered connectors...")
    await orchestrator.initialize()
    print("✅ All connectors initialized\n")
    
    # Example 1: Get all messages
    print("📨 Fetching messages from all connectors...")
    messages = await orchestrator.get_all_messages(limit=10)
    print(f"   Found {len(messages)} messages")
    for msg in messages[:3]:
        print(f"   - {msg.source_type.value}: {msg.content[:50]}...")
    print()
    
    # Example 2: Get all emails
    print("📧 Fetching emails from all connectors...")
    emails = await orchestrator.get_all_emails(limit=10, unread_only=True)
    print(f"   Found {len(emails)} unread emails")
    for email in emails[:3]:
        print(f"   - {email.source_type.value}: {email.subject[:50]}...")
    print()
    
    # Example 3: Get all notes
    print("📝 Fetching notes from all connectors...")
    notes = await orchestrator.get_all_notes(limit=10)
    print(f"   Found {len(notes)} notes")
    for note in notes[:3]:
        print(f"   - {note.source_type.value}: {note.title[:50]}...")
    print()
    
    # Example 4: Search across all sources
    print("🔍 Searching across all sources for 'meeting'...")
    search_results = await orchestrator.search_across_sources("meeting", limit=5)
    print(f"   Messages: {len(search_results['messages'])}")
    print(f"   Emails: {len(search_results['emails'])}")
    print(f"   Notes: {len(search_results['notes'])}")
    print()
    
    # Example 5: Get next actions
    print("🎯 Getting recommended next actions...")
    actions = await orchestrator.get_next_actions()
    print(f"   Found {len(actions)} recommended actions")
    for action in actions[:3]:
        print(f"   - [{action['priority']}] {action['description']}")
    print()
    
    
    # Shutdown
    print("🛑 Shutting down...")
    await orchestrator.shutdown()
    print("✅ Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())

