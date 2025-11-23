#!/usr/bin/env python3
"""
Test script to manually check email monitor functionality.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

from app.monitoring.email_monitor import EmailNotificationMonitor
from app.connectors.orchestrator import AssistantOrchestrator
from app.connectors.models import SourceType


async def test_email_fetch():
    """Test fetching emails from Outlook."""
    print("🔍 Testing Email Fetch from Outlook\n")
    
    orchestrator = AssistantOrchestrator()
    await orchestrator.initialize()
    
    # Fetch emails from last 30 minutes (wider window for testing)
    since = datetime.utcnow() - timedelta(minutes=30)
    
    print(f"Fetching emails since {since.isoformat()} (last 30 minutes)\n")
    
    emails = await orchestrator.get_all_emails(
        source_types=[SourceType.OUTLOOK],
        unread_only=True,
        limit=20
    )
    
    print(f"📧 Found {len(emails)} unread emails from Outlook\n")
    
    if emails:
        print("Recent emails:")
        for i, email in enumerate(emails[:10], 1):
            from_addr = email.from_address.get('email', 'Unknown')
            from_name = email.from_address.get('name', '')
            sender = f"{from_name} <{from_addr}>" if from_name else from_addr
            print(f"  {i}. Subject: {email.subject}")
            print(f"     From: {sender}")
            print(f"     Time: {email.timestamp}")
            print(f"     Important: {email.is_important}")
            print(f"     Priority: {email.priority.value}")
            print()
    else:
        print("❌ No emails found")
        print("\n💡 Troubleshooting:")
        print("   1. Check if you have unread emails in Outlook")
        print("   2. Verify Outlook connector is connected")
        print("   3. Check logs for errors")
    
    await orchestrator.shutdown()


async def test_email_monitor():
    """Test the email monitor directly."""
    print("\n" + "="*60)
    print("🧪 Testing Email Monitor\n")
    
    monitor = EmailNotificationMonitor(
        check_interval_seconds=300,
        lookback_minutes=30  # Wider window for testing
    )
    
    # Initialize
    await monitor.orchestrator.initialize()
    
    # Check for important emails
    print("Checking for important emails...\n")
    important_emails = await monitor._check_for_important_emails()
    
    print(f"Found {len(important_emails)} important emails\n")
    
    for email in important_emails:
        print(f"  📧 {email.subject}")
        print(f"     From: {email.from_address.get('email', 'Unknown')}")
        print(f"     Time: {email.timestamp}")
        print()
    
    await monitor.shutdown()


if __name__ == "__main__":
    print("="*60)
    print("Email Monitor Test")
    print("="*60)
    print()
    
    # Test 1: Fetch emails
    asyncio.run(test_email_fetch())
    
    # Test 2: Test monitor
    asyncio.run(test_email_monitor())

