# How to Find Your Azure OpenAI Endpoint

## Endpoint Format

Your Azure OpenAI endpoint follows this format:
```
https://YOUR-RESOURCE-NAME.openai.azure.com/
```

## Where to Find It

### Option 1: Azure Portal (Recommended)

1. **Log in to Azure Portal**
   - Go to https://portal.azure.com
   - Sign in with your Azure account

2. **Navigate to Your Azure OpenAI Resource**
   - In the search bar, type "Azure OpenAI"
   - Click on "Azure OpenAI" service
   - Select your resource from the list

3. **Get the Endpoint**
   - In the left sidebar, click on **"Keys and Endpoint"** (under "Resource Management")
   - You'll see a section called **"Endpoint"**
   - Copy the endpoint URL (it will look like: `https://your-resource-name.openai.azure.com/`)

### Option 2: Azure OpenAI Studio

1. **Open Azure OpenAI Studio**
   - Go to https://oai.azure.com
   - Select your subscription and resource

2. **Find Endpoint in Settings**
   - Click on your resource name (top left)
   - Look for "Endpoint" in the resource details
   - Copy the endpoint URL

## Example Endpoints

✅ **Correct formats:**
```
https://my-assistant.openai.azure.com/
https://contoso-ai.openai.azure.com/
https://mycompany-openai.openai.azure.com/
```

❌ **Incorrect formats:**
```
https://your-resource.openai.azure.com/  (placeholder, not real)
http://my-resource.openai.azure.com/   (missing 's' in https)
https://my-resource.openai.azure.com   (missing trailing slash)
https://my-resource.openai.azure.com/api  (extra path)
```

## Update Your .env File

Once you have your endpoint, update your `.env` file:

```bash
AZURE_OPENAI_ENDPOINT=https://YOUR-ACTUAL-RESOURCE-NAME.openai.azure.com/
```

## Verify Your Configuration

After updating, you should have:
- ✅ `USE_AZURE_OPENAI=true`
- ✅ `AZURE_OPENAI_API_KEY=your-actual-key`
- ✅ `AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/`
- ✅ `AZURE_OPENAI_DEPLOYMENT=your-deployment-name`
- ✅ `AZURE_OPENAI_WHISPER_DEPLOYMENT=whisper-1` (or your Whisper deployment)
- ✅ `AZURE_OPENAI_API_VERSION=2024-02-15-preview`

## Quick Check

Your endpoint should:
- Start with `https://`
- Contain your resource name (not "your-resource")
- End with `.openai.azure.com/`
- Have a trailing slash

## Need Help?

If you can't find your endpoint:
1. Check that you have access to the Azure OpenAI resource
2. Verify you're looking at the correct Azure subscription
3. Make sure the resource exists and is deployed
4. Contact your Azure administrator if you don't have access

