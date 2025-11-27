#!/usr/bin/env python3
"""
Direct test of Gmail connector to verify it's working.
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

from app.connectors.implementations.gmail_connector import GmailConnector
from app.connectors.models import SourceType
from datetime import datetime, timedelta


async def test_gmail_connector():
    """Test Gmail connector directly."""
    print("=" * 80)
    print("🔍 TESTING GMAIL CONNECTOR DIRECTLY")
    print("=" * 80)
    print()
    
    # Check configuration
    username = os.getenv("EMAIL_IMAP_USERNAME")
    password = os.getenv("EMAIL_IMAP_PASSWORD")
    server = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
    port = int(os.getenv("EMAIL_IMAP_PORT", "993"))
    
    print(f"📧 Configuration:")
    print(f"   Server: {server}:{port}")
    print(f"   Username: {username if username else 'NOT SET'}")
    print(f"   Password: {'SET' if password else 'NOT SET'}")
    print()
    
    if not username or not password:
        print("❌ Gmail credentials not configured!")
        print("   Set EMAIL_IMAP_USERNAME and EMAIL_IMAP_PASSWORD in .env")
        return False
    
    # Create connector
    print("🔌 Creating Gmail connector...")
    connector = GmailConnector(
        imap_server=server,
        imap_port=port,
        username=username,
        password=password
    )
    
    # Test connection
    print("🔗 Connecting to Gmail...")
    try:
        connected = await connector.connect()
        if not connected:
            print("❌ Failed to connect to Gmail")
            return False
        print("✅ Connected to Gmail successfully!")
        print()
    except Exception as e:
        print(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test fetching emails
    print("📬 Fetching emails from Gmail...")
    try:
        # Fetch last 10 emails from the last 24 hours
        since = datetime.utcnow() - timedelta(hours=24)
        print(f"   Looking for emails since: {since.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        emails = await asyncio.wait_for(
            connector.fetch_emails(limit=10, unread_only=False, since=since),
            timeout=30.0
        )
        
        print(f"✅ Successfully fetched {len(emails)} email(s) from Gmail")
        print()
        
        if emails:
            print("📧 Email Details:")
            print("-" * 80)
            for i, email in enumerate(emails[:5], 1):  # Show first 5
                print(f"{i}. Subject: {email.subject}")
                print(f"   From: {email.from_address.get('name', '')} <{email.from_address.get('email', 'Unknown')}>")
                print(f"   Date: {email.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"   Important: {email.is_important}")
                print(f"   Priority: {email.priority}")
                print()
            
            if len(emails) > 5:
                print(f"   ... and {len(emails) - 5} more email(s)")
                print()
        else:
            print("ℹ️  No emails found in the last 24 hours")
            print()
        
        # Test fetching recent emails (last 5 minutes)
        print("📬 Fetching emails from last 5 minutes...")
        recent_since = datetime.utcnow() - timedelta(minutes=5)
        recent_emails = await asyncio.wait_for(
            connector.fetch_emails(limit=10, unread_only=False, since=recent_since),
            timeout=30.0
        )
        print(f"✅ Found {len(recent_emails)} email(s) in the last 5 minutes")
        print()
        
        # Disconnect
        await connector.disconnect()
        print("✅ Disconnected from Gmail")
        print()
        
        print("=" * 80)
        print("✅ GMAIL CONNECTOR TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        return True
        
    except asyncio.TimeoutError:
        print("❌ Timeout fetching emails (30s)")
        return False
    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_gmail_connector())
    sys.exit(0 if success else 1)

