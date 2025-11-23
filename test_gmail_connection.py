#!/usr/bin/env python3
"""
Test script to connect to Gmail and verify the connection works.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from app.connectors.implementations import GmailConnector
from app.connectors.registry import get_registry
from app.connectors.models import SourceType
from app.connectors.orchestrator import AssistantOrchestrator


async def test_gmail_connection():
    """Test Gmail connection."""
    print("🔌 Testing Gmail Connection\n")
    
    # Check if Gmail is enabled
    if os.getenv("ENABLE_GMAIL", "false").lower() != "true":
        print("❌ Gmail is not enabled in .env")
        print("   Set ENABLE_GMAIL=true in .env")
        return
    
    # Check credentials
    username = os.getenv("EMAIL_IMAP_USERNAME")
    password = os.getenv("EMAIL_IMAP_PASSWORD")
    
    if not username or username == "your_email@gmail.com":
        print("❌ EMAIL_IMAP_USERNAME not configured")
        print("   Set EMAIL_IMAP_USERNAME=your_email@gmail.com in .env")
        return
    
    if not password or password == "your_app_password_here":
        print("❌ EMAIL_IMAP_PASSWORD not configured")
        print("   Set EMAIL_IMAP_PASSWORD=your_16_char_app_password in .env")
        print("   Get App Password from: https://myaccount.google.com/apppasswords")
        return
    
    print(f"📧 Connecting to: {username}")
    print("   Using IMAP server: imap.gmail.com:993\n")
    
    # Create connector
    gmail = GmailConnector()
    
    # Try to connect
    print("🔌 Attempting to connect...")
    try:
        connected = await gmail.connect()
        
        if connected:
            print("✅ Gmail connected successfully!\n")
            
            # Test fetching emails
            print("📧 Testing email fetch...")
            emails = await gmail.fetch_emails(limit=5, unread_only=False)
            print(f"   Found {len(emails)} emails\n")
            
            if emails:
                print("📋 Sample emails:")
                for i, email in enumerate(emails[:3], 1):
                    print(f"   {i}. From: {email.from_address.get('name', 'Unknown')}")
                    print(f"      Subject: {email.subject[:60]}")
                    print(f"      Date: {email.timestamp.strftime('%Y-%m-%d %H:%M')}")
                    print()
            
            # Test getting folders
            print("📁 Testing folder list...")
            folders = await gmail.get_mailbox_folders()
            print(f"   Found {len(folders)} folders:")
            for folder in folders[:5]:
                print(f"      - {folder.get('name', 'Unknown')}")
            print()
            
            # Disconnect
            await gmail.disconnect()
            print("✅ Test completed successfully!")
            
        else:
            print("❌ Failed to connect to Gmail")
            print("\n💡 Troubleshooting:")
            print("   1. Verify EMAIL_IMAP_USERNAME is your full Gmail address")
            print("   2. Verify EMAIL_IMAP_PASSWORD is a Gmail App Password (16 chars)")
            print("   3. Make sure 2-Step Verification is enabled")
            print("   4. Check logs for detailed error messages")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Check your credentials and network connection")


async def test_with_orchestrator():
    """Test Gmail connection via orchestrator."""
    print("\n" + "="*60)
    print("🧪 Testing Gmail via Orchestrator\n")
    
    # Get registry
    registry = get_registry()
    
    # Register Gmail connector
    if os.getenv("ENABLE_GMAIL", "false").lower() == "true":
        gmail = GmailConnector()
        registry.register_mail_connector(SourceType.GMAIL, gmail)
        print("✅ Registered Gmail connector")
    
    # Initialize orchestrator
    orchestrator = AssistantOrchestrator(registry=registry)
    
    print("\n🔌 Initializing connectors...")
    await orchestrator.initialize()
    
    # Get emails
    print("\n📧 Fetching emails from Gmail...")
    emails = await orchestrator.get_all_emails(
        source_types=[SourceType.GMAIL],
        limit=10,
        unread_only=True
    )
    
    print(f"   Found {len(emails)} unread emails from Gmail")
    for email in emails[:3]:
        print(f"   - {email.subject[:60]}")
    
    # Shutdown
    await orchestrator.shutdown()
    print("\n✅ Orchestrator test completed")


if __name__ == "__main__":
    print("="*60)
    print("Gmail Connection Test")
    print("="*60)
    print()
    
    # Run basic connection test
    asyncio.run(test_gmail_connection())
    
    # Run orchestrator test
    asyncio.run(test_with_orchestrator())

