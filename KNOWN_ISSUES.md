# Known Issues and Fixes

## Critical Issues Identified

### 1. Voice Transcription Problems
**Problem**: Transcription is capturing incomplete or incorrect audio
- Transcribing just "." (1 character)
- Capturing assistant's own voice ("Thank you for watching it")
- Missing the actual user question

**Root Causes**:
- Recording starts too early (captures assistant's "Yes, how can I help?" response)
- No Voice Activity Detection (VAD) - records silence and background noise
- Audio recording timing issues

**Fix Needed**:
- Add proper VAD (Voice Activity Detection) to only record when user is speaking
- Wait longer after assistant response before recording
- Filter out assistant's own voice from recording
- Add noise cancellation

### 2. Outlook Connector Errors
**Problem**: Multiple Graph API errors
- 400 Bad Request: `/me` endpoint not valid with app-only auth
- 403 Forbidden: Access denied errors

**Root Causes**:
- Old email ingestor still using `/me` endpoint
- Permissions not properly configured
- Mixed use of delegated vs app-only authentication

**Fix Needed**:
- Update email ingestor to use `/users/{userPrincipalName}` endpoint
- Ensure all connectors use consistent authentication
- Verify Azure AD permissions are correct

### 3. Reminder Scheduler Validation Errors
**Problem**: Task validation errors in reminder scheduler

**Fix Needed**:
- Check Task model validation requirements
- Ensure all required fields are present

### 4. Audio Recording Timing
**Problem**: Recording window may not align with user speech
- 6 seconds may be too long (captures background noise)
- Or too short (cuts off user's question)
- No adaptive recording based on speech detection

**Fix Needed**:
- Implement proper VAD (Voice Activity Detection)
- Adaptive recording duration based on speech
- Better silence detection

## Fixes Applied ✅

### ✅ Fixed - Voice Recording Issues
1. **Added Voice Activity Detection (VAD)** - Energy-based detection to only record when user speaks
2. **Fixed audio recording timing** - Properly waits for TTS to complete, skips initial frames
3. **Adaptive recording** - Stops when silence detected (max 6.5 seconds)

### ✅ Fixed - Outlook Connector
1. **Updated email ingestor** - Now uses `/users/{userPrincipalName}` endpoint for app-only auth
2. **Falls back to `/me`** - For delegated authentication when user principal not available
3. **Fixed both endpoints** - `get_messages()` and `get_message_content()`

### ✅ Fixed - Reminder Scheduler
1. **Added task validation** - Validates tasks before creating reminders
2. **Skips invalid tasks** - Handles missing/empty titles gracefully
3. **Better error handling** - Full traceback logging for debugging

## Remaining Improvements (Optional)

### Medium Priority
1. **Add noise cancellation** - Filter background noise for better transcription
2. **Improve VAD sensitivity** - Fine-tune energy threshold based on testing
3. **Add transcription confidence** - Reject low-confidence transcriptions

### Low Priority
7. **Add transcription confidence scores** - Reject low-confidence transcriptions
8. **Improve logging** - Better debugging information

## Quick Wins

1. **Increase wait time after wake word response** - Already done (1.5s)
2. **Add transcription validation** - Already done (warns if too short)
3. **Better error messages** - Help user understand what went wrong

