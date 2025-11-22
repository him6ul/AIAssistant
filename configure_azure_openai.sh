#!/bin/bash

# Script to configure Azure OpenAI in .env file

cd "$(dirname "$0")/.."

echo "🔧 Azure OpenAI Configuration"
echo "=============================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    touch .env
fi

# Enable Azure OpenAI
if grep -q "USE_AZURE_OPENAI" .env; then
    sed -i '' 's/USE_AZURE_OPENAI=.*/USE_AZURE_OPENAI=true/' .env
else
    echo "USE_AZURE_OPENAI=true" >> .env
fi

echo "✅ Set USE_AZURE_OPENAI=true"
echo ""
echo "Please provide the following Azure OpenAI credentials:"
echo ""

read -p "Azure OpenAI API Key: " azure_key
read -p "Azure OpenAI Endpoint (e.g., https://your-resource.openai.azure.com/): " azure_endpoint
read -p "Azure OpenAI Deployment Name (e.g., gpt-4-turbo): " azure_deployment
read -p "Azure OpenAI Whisper Deployment (optional, press Enter for whisper-1): " azure_whisper
read -p "Azure OpenAI API Version (press Enter for 2024-02-15-preview): " azure_version

azure_whisper=${azure_whisper:-whisper-1}
azure_version=${azure_version:-2024-02-15-preview}

# Update or add Azure OpenAI settings
if grep -q "AZURE_OPENAI_API_KEY" .env; then
    sed -i '' "s|AZURE_OPENAI_API_KEY=.*|AZURE_OPENAI_API_KEY=$azure_key|" .env
else
    echo "AZURE_OPENAI_API_KEY=$azure_key" >> .env
fi

if grep -q "AZURE_OPENAI_ENDPOINT" .env; then
    sed -i '' "s|AZURE_OPENAI_ENDPOINT=.*|AZURE_OPENAI_ENDPOINT=$azure_endpoint|" .env
else
    echo "AZURE_OPENAI_ENDPOINT=$azure_endpoint" >> .env
fi

if grep -q "AZURE_OPENAI_DEPLOYMENT" .env; then
    sed -i '' "s|AZURE_OPENAI_DEPLOYMENT=.*|AZURE_OPENAI_DEPLOYMENT=$azure_deployment|" .env
else
    echo "AZURE_OPENAI_DEPLOYMENT=$azure_deployment" >> .env
fi

if grep -q "AZURE_OPENAI_WHISPER_DEPLOYMENT" .env; then
    sed -i '' "s|AZURE_OPENAI_WHISPER_DEPLOYMENT=.*|AZURE_OPENAI_WHISPER_DEPLOYMENT=$azure_whisper|" .env
else
    echo "AZURE_OPENAI_WHISPER_DEPLOYMENT=$azure_whisper" >> .env
fi

if grep -q "AZURE_OPENAI_API_VERSION" .env; then
    sed -i '' "s|AZURE_OPENAI_API_VERSION=.*|AZURE_OPENAI_API_VERSION=$azure_version|" .env
else
    echo "AZURE_OPENAI_API_VERSION=$azure_version" >> .env
fi

echo ""
echo "✅ Azure OpenAI configuration added to .env"
echo ""
echo "📋 Configuration:"
echo "   USE_AZURE_OPENAI=true"
echo "   AZURE_OPENAI_ENDPOINT=$azure_endpoint"
echo "   AZURE_OPENAI_DEPLOYMENT=$azure_deployment"
echo "   AZURE_OPENAI_WHISPER_DEPLOYMENT=$azure_whisper"
echo "   AZURE_OPENAI_API_VERSION=$azure_version"
echo ""
echo "🔄 Please restart the backend to apply changes:"
echo "   pkill -f app.main"
echo "   ./scripts/run_backend.sh"

