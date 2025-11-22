# Azure OpenAI Setup Guide

## Why Use Azure OpenAI?

Azure OpenAI can help resolve authentication and API key issues, and provides:
- Enterprise-grade security and compliance
- Better error handling
- Data residency options
- Private endpoints

## Setup Instructions

### Step 1: Get Azure OpenAI Credentials

1. **Create Azure OpenAI Resource**:
   - Go to Azure Portal: https://portal.azure.com
   - Create a new "Azure OpenAI" resource
   - Note your endpoint URL (e.g., `https://your-resource.openai.azure.com/`)

2. **Get Your API Key**:
   - In Azure Portal, go to your Azure OpenAI resource
   - Navigate to "Keys and Endpoint"
   - Copy one of the keys (KEY 1 or KEY 2)

3. **Create Deployments**:
   - Go to "Deployments" in your Azure OpenAI resource
   - Create deployments for:
     - Chat model (e.g., `gpt-4-turbo` or `gpt-35-turbo`)
     - Whisper model (e.g., `whisper-1`) - for speech-to-text

### Step 2: Configure Your .env File

Add these lines to your `.env` file:

```bash
# Enable Azure OpenAI
USE_AZURE_OPENAI=true

# Azure OpenAI Credentials
AZURE_OPENAI_API_KEY=your-azure-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo  # Your chat model deployment name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_WHISPER_DEPLOYMENT=whisper-1  # Your Whisper deployment name (optional)
```

### Step 3: Restart the Backend

```bash
# Stop the backend
pkill -f app.main

# Start it again
./scripts/run_backend.sh
```

## Configuration Details

### Required Variables

- `USE_AZURE_OPENAI=true` - Enables Azure OpenAI mode
- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint URL
- `AZURE_OPENAI_DEPLOYMENT` - Your chat model deployment name

### Optional Variables

- `AZURE_OPENAI_API_VERSION` - API version (default: `2024-02-15-preview`)
- `AZURE_OPENAI_WHISPER_DEPLOYMENT` - Whisper deployment name (default: `whisper-1`)

## Switching Back to Standard OpenAI

To switch back to standard OpenAI, set:

```bash
USE_AZURE_OPENAI=false
OPENAI_API_KEY=sk-your-standard-key
```

Or remove the Azure configuration variables.

## Troubleshooting

### Error: "Invalid API key"
- Verify your Azure OpenAI API key is correct
- Make sure you're using the key from Azure Portal (not OpenAI platform)

### Error: "Deployment not found"
- Check that your deployment name matches exactly
- Verify the deployment exists in your Azure OpenAI resource
- Ensure the deployment is in "Succeeded" state

### Error: "Endpoint not found"
- Verify your endpoint URL is correct
- Make sure it includes `https://` and ends with `/`
- Check that your Azure OpenAI resource is active

## Benefits Over Standard OpenAI

1. **Better Error Messages**: Azure provides more detailed error information
2. **Enterprise Security**: Data stays within your Azure tenant
3. **Rate Limits**: Separate from standard OpenAI rate limits
4. **Compliance**: Meets enterprise compliance requirements
5. **Private Endpoints**: Can use private networking

## Testing

After configuration, test with:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, test message"}'
```

Check logs to see:
```
Initialized Azure OpenAI client: https://your-resource.openai.azure.com/
```

