# Fix Plan for Voice Assistant Issues

## Issues Identified

### 1. **Voice Transcription Problems** (CRITICAL)
- **Symptom**: Transcribing "." or "Thank you for watching it" instead of user's question
- **Root Cause**: 
  - Recording assistant's own voice ("Yes, how can I help?")
  - No Voice Activity Detection (VAD)
  - Fixed 6-second recording captures silence/background noise
- **Impact**: Assistant cannot understand user commands

### 2. **Outlook Connector Errors** (HIGH)
- **Symptom**: 400/403 errors from Graph API
- **Root Cause**: Old email ingestor using `/me` endpoint with app-only auth
- **Impact**: Email monitoring not working

### 3. **Reminder Scheduler Errors** (MEDIUM)
- **Symptom**: Task validation errors
- **Impact**: Reminders not working

## Immediate Fixes

### Fix 1: Proper TTS Completion Wait
**Problem**: `speak()` is called but we don't wait for it to finish before recording
**Solution**: Use async executor and wait for completion

### Fix 2: Better Audio Recording
**Problem**: Fixed 6-second window captures everything
**Solution**: 
- Wait longer after TTS completes
- Add simple energy-based VAD (detect when user starts speaking)
- Stop recording when silence detected

### Fix 3: Filter Assistant's Voice
**Problem**: Recording picks up assistant's own response
**Solution**: 
- Ensure TTS fully completes before recording
- Add buffer time after TTS
- Skip initial frames that might contain TTS echo

## Implementation Priority

1. **Fix TTS wait** - Ensure assistant finishes speaking before recording
2. **Add simple VAD** - Only record when user is actually speaking
3. **Fix Outlook connector** - Update email ingestor endpoints
4. **Improve error handling** - Better user feedback

