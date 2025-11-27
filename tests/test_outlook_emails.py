#!/usr/bin/env python3
"""
Test script to fetch last 5 emails from Outlook, check importance, and notify.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

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


async def test_outlook_emails():
    """Test fetching and checking Outlook emails."""
    print("="*60)
    print("Testing Outlook Email Fetching and Importance Detection")
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
    
    # Fetch last 5 emails from Outlook (not just unread)
    print("📧 Fetching last 5 emails from Outlook...")
    emails = await orchestrator.get_all_emails(
        source_types=[SourceType.OUTLOOK],
        unread_only=False,  # Get all emails, not just unread
        limit=5
    )
    
    print(f"✅ Found {len(emails)} emails from Outlook\n")
    
    if not emails:
        print("❌ No emails found in Outlook")
        print("\n💡 Troubleshooting:")
        print("   1. Check if Outlook connector is connected")
        print("   2. Verify you have emails in your Outlook inbox")
        print("   3. Check logs for errors")
        await orchestrator.shutdown()
        return
    
    # Display all emails
    print("📋 Email Details:")
    print("-" * 60)
    for i, email in enumerate(emails, 1):
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
    for email in emails:
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
        asyncio.run(test_outlook_emails())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

