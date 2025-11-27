#!/usr/bin/env python3
"""
Test script to fetch last 5 emails from Gmail, check importance, and notify.
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

from app.connectors.orchestrator import AssistantOrchestrator
from app.connectors.models import SourceType
from app.connectors.loader import load_connectors, initialize_connectors
from app.monitoring.email_monitor import EmailImportanceChecker
from app.tts import TTSEngine
from app.utils.localization import get_message


async def test_gmail_emails():
    """Test fetching and checking Gmail emails."""
    print("="*60)
    print("Testing Gmail Email Fetching and Importance Detection")
    print("="*60)
    print()
    
    # Load and initialize connectors first
    print("📦 Loading connectors...")
    load_connectors()
    print("✅ Connectors loaded")
    
    print("🔌 Initializing connectors...")
    await initialize_connectors()
    print("✅ Connectors initialized\n")
    
    # Initialize orchestrator (will use the loaded connectors)
    print("🔌 Initializing orchestrator...")
    orchestrator = AssistantOrchestrator()
    await orchestrator.initialize()
    print("✅ Orchestrator initialized\n")
    
    # Fetch last 10 emails from Gmail (not just unread)
    print("📧 Fetching emails from Gmail...")
    
    emails = await orchestrator.get_all_emails(
        source_types=[SourceType.GMAIL],
        unread_only=False,  # Get all emails, not just unread
        limit=10
    )
    
    print(f"✅ Found {len(emails)} total emails\n")
    
    # Show all emails regardless of time
    recent_emails = emails
    
    if not recent_emails:
        print("❌ No recent emails found in Gmail")
        print("\n💡 Troubleshooting:")
        print("   1. Check if Gmail connector is connected")
        print("   2. Verify you have emails in your Gmail inbox")
        print("   3. Check if emails are from the last 30 minutes")
        await orchestrator.shutdown()
        return
    
    # Display all emails
    print("📋 Email Details:")
    print("-" * 60)
    for i, email in enumerate(recent_emails, 1):
        from_addr = email.from_address.get('email', 'Unknown')
        from_name = email.from_address.get('name', '')
        sender = f"{from_name} <{from_addr}>" if from_name else from_addr
        
        print(f"\n{i}. Subject: {email.subject}")
        print(f"   From: {sender}")
        print(f"   Time: {email.timestamp}")
        print(f"   Read: {'Yes' if email.is_read else 'No'}")
        print(f"   Important Flag: {email.is_important}")
        print(f"   Priority: {email.priority.value}")
        if email.body_text:
            preview = email.body_text[:100].replace('\n', ' ')
            print(f"   Preview: {preview}...")
    
    print("\n" + "-" * 60)
    
    # Check importance for each email
    print("\n🔍 Checking email importance...")
    importance_checker = EmailImportanceChecker()
    
    important_emails = []
    for email in recent_emails:
        print(f"\nChecking: '{email.subject}'")
        is_important = await importance_checker.is_important(email)
        print(f"  → Important: {is_important}")
        
        if is_important:
            important_emails.append(email)
    
    print(f"\n✅ Found {len(important_emails)} important email(s)\n")
    
    # Notify about important emails
    if important_emails:
        print("🔔 Playing notification for important emails...\n")
        
        tts_engine = TTSEngine()
        user_name = os.getenv("USER_NAME", "Himanshu")
        
        for email in important_emails:
            sender_name = email.from_address.get("name") or email.from_address.get("email", "Unknown")
            subject = email.subject or "No subject"
            
            # Get localized message
            prefix = get_message("EMAIL_NOTIFICATION_PREFIX", user_name=user_name)
            subject_line = get_message("EMAIL_NOTIFICATION_SUBJECT", subject=subject)
            from_line = get_message("EMAIL_NOTIFICATION_FROM", sender=sender_name)
            
            # Build notification message
            notification = f"{prefix}. {subject_line}. {from_line}."
            
            print(f"📢 Speaking: {notification}")
            
            # Speak the notification
            await asyncio.to_thread(tts_engine.speak, notification)
            
            # Small delay between notifications
            await asyncio.sleep(2)
        
        print("\n✅ Notifications played successfully!")
    else:
        print("ℹ️  No important emails found - no notification needed")
    
    # Cleanup
    await orchestrator.shutdown()
    print("\n✅ Test completed")


if __name__ == "__main__":
    try:
        asyncio.run(test_gmail_emails())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

