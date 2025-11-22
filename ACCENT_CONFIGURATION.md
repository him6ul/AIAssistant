# Accent/Language Configuration Guide

## Overview
The assistant uses OpenAI Whisper API for speech-to-text transcription. You can configure the language/accent to improve recognition accuracy.

## How to Configure

### Step 1: Add to .env file
Add the following line to your `.env` file:
```env
STT_LANGUAGE=en-IN
```

### Step 2: Choose Your Language Code

#### English Variants (for accents):
- `en` - English (auto-detect, may be less accurate)
- `en-US` - US English
- `en-GB` - British English  
- `en-IN` - Indian English
- `en-AU` - Australian English
- `en-CA` - Canadian English
- `en-NZ` - New Zealand English
- `en-ZA` - South African English

#### Other Languages:
- `hi` - Hindi
- `es` - Spanish
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `zh` - Chinese
- `ja` - Japanese
- `ko` - Korean
- `ar` - Arabic
- `ru` - Russian

### Step 3: Restart the Server
After adding `STT_LANGUAGE` to your `.env` file, restart the server:
```bash
# Stop the server
pkill -9 -f "python.*app.main"

# Start the server
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
source venv/bin/activate
python -m app.main
```

## How It Works

1. **Language Parameter**: The Whisper API accepts a language code parameter
2. **Better Accuracy**: Specifying the language helps the model focus on that language/accent
3. **Auto-Detection**: If `STT_LANGUAGE` is not set, Whisper will auto-detect (may be less accurate for accents)

## Testing

After configuration, test by:
1. Saying "Hey Jarvis"
2. Speaking a command with your accent
3. Check if transcription is more accurate

## Troubleshooting

- **Still not accurate?** Try a more specific variant (e.g., `en-IN` instead of `en`)
- **Wrong language detected?** Make sure `STT_LANGUAGE` is set correctly in `.env`
- **No improvement?** The Whisper model may need more training data for your specific accent

## Notes

- Language codes follow ISO 639-1 standard
- Region codes (like `-US`, `-GB`) help with accent recognition
- If you speak multiple languages, you may need to switch `STT_LANGUAGE` based on context

## Multiple Accents Support

You can specify multiple language codes (comma-separated) to support multiple accents. The system will try them in order until one works.

### Example Configuration

```env
# Support both Indian and US English accents
STT_LANGUAGE=en-IN,en-US

# Support British, Australian, and US English
STT_LANGUAGE=en-GB,en-AU,en-US

# Support Hindi and English
STT_LANGUAGE=hi,en
```

### How It Works

1. **Primary Language**: The first language code is used as the primary
2. **Fallback**: If transcription fails or seems inaccurate, the system tries the next language code
3. **Order Matters**: List languages in order of preference (most common first)

### Use Cases

- **Multiple Accents**: If you speak with different accents (e.g., Indian English sometimes, US English other times)
- **Code-Switching**: If you mix languages (e.g., Hindi and English)
- **Family/Team**: If multiple people with different accents use the assistant

### Tips

- Start with your most common accent first
- You can include just the base language (e.g., `en`) as a fallback
- Auto-detection (no STT_LANGUAGE) works well but may be less accurate for specific accents

## Important: Language Code Format

**OpenAI Whisper API Limitation:**
- Whisper API only accepts **ISO-639-1 base language codes** (e.g., `en`, `hi`, `es`)
- Region-specific codes (e.g., `en-US`, `en-IN`, `en-GB`) are **automatically converted** to base codes
- Example: `en-IN` → `en`, `en-US` → `en`

**What This Means:**
- You can still use region codes in `STT_LANGUAGE` (e.g., `en-IN,en-US`)
- The system automatically converts them to base codes (`en`)
- Whisper model is trained on various accents and should handle them
- For best accent recognition, consider using auto-detection (leave `STT_LANGUAGE` empty)

**Recommended Configuration:**
- **For single language with accent**: `STT_LANGUAGE=en` (or leave empty for auto-detect)
- **For multiple languages**: `STT_LANGUAGE=hi,en` (Hindi and English)
- **For accent fallback**: `STT_LANGUAGE=en` (Whisper handles accents automatically)
