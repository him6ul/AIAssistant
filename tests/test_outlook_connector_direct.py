import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

load_dotenv()

from app.connectors.implementations.outlook_connector import OutlookConnector
from app.connectors.models import UnifiedEmail, SourceType
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def test_outlook_connector_direct():
    print("================================================================================")
    print("🔍 TESTING OUTLOOK CONNECTOR DIRECTLY")
    print("================================================================================")

    client_id = os.getenv("MS_CLIENT_ID")
    client_secret = os.getenv("MS_CLIENT_SECRET")
    tenant_id = os.getenv("MS_TENANT_ID")
    user_principal_name = os.getenv("MS_USER_PRINCIPAL_NAME")

    print(f"\n📧 Configuration:")
    print(f"   Client ID: {client_id[:20] + '...' if client_id and len(client_id) > 20 else client_id}")
    print(f"   Client Secret: {'SET' if client_secret else 'NOT SET'}")
    print(f"   Tenant ID: {tenant_id}")
    print(f"   User Principal Name: {user_principal_name}")

    if not client_id or not client_secret or not tenant_id:
        print("\n❌ Outlook credentials not properly configured in .env.")
        print("   Please set MS_CLIENT_ID, MS_CLIENT_SECRET, and MS_TENANT_ID.")
        return

    if not user_principal_name:
        print("\n⚠️  MS_USER_PRINCIPAL_NAME not set. Will attempt to auto-detect...")

    print("\n🔌 Creating Outlook connector...")
    connector = OutlookConnector(
        client_id=client_id,
        client_secret=client_secret,
        tenant_id=tenant_id
    )

    print("🔗 Connecting to Outlook...")
    connected = await connector.connect()
    if not connected:
        print("❌ Failed to connect to Outlook.")
        return

    print("✅ Connected to Outlook successfully!")

    print("\n📬 Fetching emails from Outlook...")
    since = datetime.utcnow() - timedelta(hours=24)
    print(f"   Looking for emails since: {since.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    try:
        emails: List[UnifiedEmail] = await connector.fetch_emails(limit=10, since=since)
        
        if emails:
            print(f"✅ Successfully fetched {len(emails)} email(s) from Outlook")
            print("\n📧 Email Details:")
            print("--------------------------------------------------------------------------------")
            for i, email_obj in enumerate(emails, 1):
                print(f"{i}. Subject: {email_obj.subject}")
                print(f"   From: {email_obj.from_address.get('name', '')} <{email_obj.from_address.get('email', '')}>")
                print(f"   Date: {email_obj.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"   Important: {email_obj.is_important}")
                print(f"   Priority: {email_obj.priority}")
                print(f"   ID: {email_obj.id}")
                if i < 5 and len(emails) > 5:  # Show first 5, then summarize
                    pass
                elif i == 5 and len(emails) > 5:
                    print(f"\n   ... and {len(emails) - 5} more email(s)\n")
                    break
                print("")
        else:
            print("❌ No emails fetched from Outlook.")
    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n📬 Fetching emails from last 5 minutes...")
    recent_since = datetime.utcnow() - timedelta(minutes=5)
    try:
        recent_emails = await connector.fetch_emails(limit=10, since=recent_since)
        print(f"✅ Found {len(recent_emails)} email(s) in the last 5 minutes")
    except Exception as e:
        print(f"❌ Error fetching recent emails: {e}")
        import traceback
        traceback.print_exc()

    print("\n✅ Disconnected from Outlook")
    await connector.disconnect()

    print("\n================================================================================")
    print("✅ OUTLOOK CONNECTOR TEST COMPLETED")
    print("================================================================================")

if __name__ == "__main__":
    asyncio.run(test_outlook_connector_direct())

