#!/usr/bin/env python3
"""
Test script to connect to Outlook and verify the connection works.
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

from app.connectors.implementations import OutlookConnector
from app.connectors.registry import get_registry
from app.connectors.models import SourceType
from app.connectors.orchestrator import AssistantOrchestrator


async def test_outlook_connection():
    """Test Outlook connection."""
    print("🔌 Testing Outlook Connection\n")
    
    # Check if Outlook is enabled
    if os.getenv("ENABLE_OUTLOOK", "false").lower() != "true":
        print("❌ Outlook is not enabled in .env")
        print("   Set ENABLE_OUTLOOK=true in .env")
        return
    
    # Check credentials
    client_id = os.getenv("MS_CLIENT_ID")
    client_secret = os.getenv("MS_CLIENT_SECRET")
    tenant_id = os.getenv("MS_TENANT_ID")
    
    if not client_id or client_id == "your_azure_client_id_here":
        print("❌ MS_CLIENT_ID not configured")
        print("   Set MS_CLIENT_ID=your_azure_client_id in .env")
        print("   Get it from: Azure Portal → App registrations → Your app → Application (client) ID")
        return
    
    if not client_secret or client_secret == "your_azure_client_secret_here":
        print("❌ MS_CLIENT_SECRET not configured")
        print("   Set MS_CLIENT_SECRET=your_client_secret in .env")
        print("   Get it from: Azure Portal → App registrations → Your app → Certificates & secrets")
        return
    
    if not tenant_id or tenant_id == "your_tenant_id_here":
        print("❌ MS_TENANT_ID not configured")
        print("   Set MS_TENANT_ID=your_tenant_id in .env")
        print("   Get it from: Azure Portal → App registrations → Your app → Directory (tenant) ID")
        return
    
    print(f"📧 Connecting to Outlook...")
    print(f"   Client ID: {client_id[:8]}...")
    print(f"   Tenant ID: {tenant_id}\n")
    
    # Create connector
    outlook = OutlookConnector()
    
    # Try to connect
    print("🔌 Attempting to connect...")
    try:
        connected = await outlook.connect()
        
        if connected:
            print("✅ Outlook connected successfully!\n")
            
            # Test fetching emails
            print("📧 Testing email fetch...")
            emails = await outlook.fetch_emails(limit=5, unread_only=False)
            print(f"   Found {len(emails)} emails\n")
            
            if emails:
                print("📋 Sample emails:")
                for i, email in enumerate(emails[:3], 1):
                    from_addr = email.from_address.get('name', email.from_address.get('email', 'Unknown'))
                    print(f"   {i}. From: {from_addr}")
                    print(f"      Subject: {email.subject[:60]}")
                    print(f"      Date: {email.timestamp.strftime('%Y-%m-%d %H:%M')}")
                    print()
            
            # Test getting folders
            print("📁 Testing folder list...")
            folders = await outlook.get_mailbox_folders()
            print(f"   Found {len(folders)} folders:")
            for folder in folders[:5]:
                print(f"      - {folder.get('name', 'Unknown')}")
            print()
            
            # Disconnect
            await outlook.disconnect()
            print("✅ Test completed successfully!")
            
        else:
            print("❌ Failed to connect to Outlook")
            print("\n💡 Troubleshooting:")
            print("   1. Verify MS_CLIENT_ID is your Application (client) ID")
            print("   2. Verify MS_CLIENT_SECRET is the secret Value (not ID)")
            print("   3. Verify MS_TENANT_ID is your Directory (tenant) ID")
            print("   4. Check API permissions are granted in Azure Portal")
            print("   5. Check admin consent is granted (if required)")
            print("   6. Check logs for detailed error messages")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Check your credentials and API permissions in Azure Portal")


async def test_with_orchestrator():
    """Test Outlook connection via orchestrator."""
    print("\n" + "="*60)
    print("🧪 Testing Outlook via Orchestrator\n")
    
    # Get registry
    registry = get_registry()
    
    # Register Outlook connector
    if os.getenv("ENABLE_OUTLOOK", "false").lower() == "true":
        outlook = OutlookConnector()
        registry.register_mail_connector(SourceType.OUTLOOK, outlook)
        print("✅ Registered Outlook connector")
    
    # Initialize orchestrator
    orchestrator = AssistantOrchestrator(registry=registry)
    
    print("\n🔌 Initializing connectors...")
    await orchestrator.initialize()
    
    # Get emails
    print("\n📧 Fetching emails from Outlook...")
    emails = await orchestrator.get_all_emails(
        source_types=[SourceType.OUTLOOK],
        limit=10,
        unread_only=True
    )
    
    print(f"   Found {len(emails)} unread emails from Outlook")
    for email in emails[:3]:
        print(f"   - {email.subject[:60]}")
    
    # Shutdown
    await orchestrator.shutdown()
    print("\n✅ Orchestrator test completed")


if __name__ == "__main__":
    print("="*60)
    print("Outlook Connection Test")
    print("="*60)
    print()
    
    # Run basic connection test
    asyncio.run(test_outlook_connection())
    
    # Run orchestrator test
    asyncio.run(test_with_orchestrator())

