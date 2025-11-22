#!/usr/bin/env python3
"""
Test script to verify Azure OpenAI configuration and initialization.
"""

import os
import sys
from dotenv import load_dotenv

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

print("🧪 Testing Azure OpenAI Configuration")
print("=" * 60)
print()

# Check configuration
use_azure = os.getenv("USE_AZURE_OPENAI", "false").lower() == "true"
azure_key = os.getenv("AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
openai_key = os.getenv("OPENAI_API_KEY")

print("📋 Configuration Status:")
print(f"  USE_AZURE_OPENAI: {use_azure}")
print(f"  AZURE_OPENAI_API_KEY: {'✅ Set' if azure_key else '❌ Not set'}")
print(f"  AZURE_OPENAI_ENDPOINT: {azure_endpoint or '❌ Not set'}")
print(f"  AZURE_OPENAI_DEPLOYMENT: {azure_deployment or '❌ Not set'}")
print(f"  OPENAI_API_KEY: {'✅ Set' if openai_key else '❌ Not set'}")
print()

if use_azure:
    print("✅ Azure OpenAI mode is ENABLED")
    print()
    
    # Check if all required Azure config is present
    if not azure_key:
        print("❌ ERROR: AZURE_OPENAI_API_KEY is required but not set")
        sys.exit(1)
    
    if not azure_endpoint:
        print("❌ ERROR: AZURE_OPENAI_ENDPOINT is required but not set")
        sys.exit(1)
    
    if not azure_deployment:
        print("⚠️  WARNING: AZURE_OPENAI_DEPLOYMENT not set, will use default")
    
    print("✅ All required Azure OpenAI configuration is present")
    print()
    
    # Test initialization
    print("🔧 Testing LLM Router initialization...")
    try:
        from app.llm_router import get_llm_router
        router = get_llm_router()
        
        if router.use_azure:
            print(f"✅ LLM Router initialized with Azure OpenAI")
            print(f"   Endpoint: {router.azure_endpoint}")
            print(f"   Deployment: {router.openai_model}")
            print(f"   API Version: {router.azure_api_version}")
        else:
            print("❌ LLM Router is NOT using Azure (check configuration)")
    except Exception as e:
        print(f"❌ Error initializing LLM Router: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🔧 Testing STT Engine initialization...")
    try:
        from app.stt import get_stt_engine
        stt = get_stt_engine()
        
        if stt.use_azure:
            print(f"✅ STT Engine initialized with Azure OpenAI")
            print(f"   Endpoint: {stt.azure_endpoint}")
        else:
            print("⚠️  STT Engine is NOT using Azure (will use standard OpenAI)")
    except Exception as e:
        print(f"❌ Error initializing STT Engine: {e}")
        import traceback
        traceback.print_exc()
    
else:
    print("ℹ️  Azure OpenAI mode is DISABLED")
    print("   Using standard OpenAI API")
    print()
    print("💡 To enable Azure OpenAI, add to .env:")
    print("   USE_AZURE_OPENAI=true")
    print("   AZURE_OPENAI_API_KEY=your-key")
    print("   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/")
    print("   AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo")

print()
print("=" * 60)
print("✅ Test complete!")

