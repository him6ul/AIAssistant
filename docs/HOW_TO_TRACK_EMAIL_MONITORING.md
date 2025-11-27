# How to Track Email Monitoring

The assistant now has comprehensive logging to track Gmail and Outlook email monitoring. Here's how to check if it's working.

## Log Files

The assistant writes logs to:
- **Main log file**: `logs/assistant.log` (or as configured in `config/config.yaml`)
- All email monitoring activity is logged with clear markers

## What Gets Logged

### 1. Monitor Startup
When the email monitor starts, you'll see:
```
🚀 STARTING EMAIL NOTIFICATION MONITOR
   Check interval: 300s (5.0 minutes)
   Lookback window: 5 minutes
   Tracking X previously notified emails
```

### 2. Each Check Cycle
Every 5 minutes, you'll see a detailed log entry:
```
📧 EMAIL MONITOR CHECK STARTED at YYYY-MM-DD HH:MM:SS UTC
   Checking for emails since: YYYY-MM-DD HH:MM:SS UTC
   Lookback window: 5 minutes
   Sources to check: Gmail, Outlook
```

### 3. Email Fetching
For each source (Gmail/Outlook):
```
📬 UnifiedInboxService: Fetching emails from X registered mail connector(s)
   🔍 Checking gmail connector...
   ✅ gmail is connected, fetching emails...
   ✅ Fetched X emails from gmail in Y.XXs
```

### 4. Email Details
For each recent email found:
```
📋 Recent emails details:
   1. [gmail] 'Subject' from sender@example.com at YYYY-MM-DD HH:MM:SS UTC
      ID: gmail_123, Important flag: True, Priority: HIGH
```

### 5. Importance Checking
For each email being checked:
```
   [1/5] Checking: 'Subject' from sender@example.com
      - Source: gmail
      - Timestamp: YYYY-MM-DD HH:MM:SS UTC
      - Is Important Flag: True
      - Priority: HIGH
      ✅ RESULT: IMPORTANT - Will notify user
```

### 6. Notifications
When an important email is found:
```
🔔 NOTIFICATION PHASE
   Found 1 new important email(s) to notify about
   🔊 Speaking notification for email: 'Subject' from sender@example.com
   ✅ Notification completed and email marked as notified
```

## How to Check Logs

### Option 1: View Log File Directly
```bash
# View the entire log file
cat logs/assistant.log

# View last 100 lines
tail -n 100 logs/assistant.log

# Follow the log in real-time (watch as new entries are added)
tail -f logs/assistant.log
```

### Option 2: Search for Email Monitoring Entries
```bash
# Search for email monitor check cycles
grep "EMAIL MONITOR CHECK STARTED" logs/assistant.log

# Search for Gmail fetching
grep "gmail" logs/assistant.log -i

# Search for important emails found
grep "IMPORTANT" logs/assistant.log

# Search for notifications
grep "NOTIFICATION" logs/assistant.log

# Search for errors
grep "ERROR\|❌" logs/assistant.log
```

### Option 3: Filter Recent Activity
```bash
# Show last 50 lines with email monitoring activity
tail -n 50 logs/assistant.log | grep -E "EMAIL|📧|📬|🔍|✅|❌|🔔"

# Show all check cycles from today
grep "$(date +%Y-%m-%d)" logs/assistant.log | grep "EMAIL MONITOR"
```

## Quick Status Check Script

Create a script to quickly check email monitoring status:

```bash
#!/bin/bash
# check_email_monitor.sh

LOG_FILE="logs/assistant.log"

echo "📊 Email Monitor Status Check"
echo "=============================="
echo ""

# Check if monitor started
if grep -q "STARTING EMAIL NOTIFICATION MONITOR" "$LOG_FILE"; then
    echo "✅ Monitor is running"
    LAST_START=$(grep "STARTING EMAIL NOTIFICATION MONITOR" "$LOG_FILE" | tail -1)
    echo "   Last start: $LAST_START"
else
    echo "❌ Monitor has not started"
fi

echo ""

# Count check cycles
CHECK_COUNT=$(grep -c "EMAIL MONITOR CHECK STARTED" "$LOG_FILE" 2>/dev/null || echo "0")
echo "📧 Total check cycles: $CHECK_COUNT"

# Last check time
LAST_CHECK=$(grep "EMAIL MONITOR CHECK STARTED" "$LOG_FILE" | tail -1 | cut -d' ' -f1-2)
if [ -n "$LAST_CHECK" ]; then
    echo "   Last check: $LAST_CHECK"
else
    echo "   No checks found yet"
fi

echo ""

# Gmail status
GMAIL_FETCHES=$(grep -c "Fetched.*emails from gmail" "$LOG_FILE" 2>/dev/null || echo "0")
echo "📬 Gmail fetches: $GMAIL_FETCHES"

# Outlook status
OUTLOOK_FETCHES=$(grep -c "Fetched.*emails from outlook" "$LOG_FILE" 2>/dev/null || echo "0")
echo "📬 Outlook fetches: $OUTLOOK_FETCHES"

echo ""

# Important emails found
IMPORTANT_COUNT=$(grep -c "RESULT: IMPORTANT" "$LOG_FILE" 2>/dev/null || echo "0")
echo "🎯 Important emails detected: $IMPORTANT_COUNT"

# Notifications sent
NOTIFICATION_COUNT=$(grep -c "Speaking notification" "$LOG_FILE" 2>/dev/null || echo "0")
echo "🔔 Notifications sent: $NOTIFICATION_COUNT"

echo ""

# Recent errors
ERROR_COUNT=$(grep -c "❌ ERROR" "$LOG_FILE" 2>/dev/null || echo "0")
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "⚠️  Errors found: $ERROR_COUNT"
    echo "   Recent errors:"
    grep "❌ ERROR" "$LOG_FILE" | tail -3 | sed 's/^/      /'
else
    echo "✅ No errors found"
fi

echo ""
echo "=============================="
echo "View full log: tail -f $LOG_FILE"
```

Save this as `scripts/check_email_monitor.sh` and make it executable:
```bash
chmod +x scripts/check_email_monitor.sh
./scripts/check_email_monitor.sh
```

## What to Look For

### ✅ Healthy Operation
- Regular check cycles every 5 minutes
- Successful Gmail/Outlook fetches
- Emails being checked for importance
- No errors

### ⚠️ Potential Issues

1. **No check cycles appearing**
   - Monitor may not have started
   - Check if Gmail/Outlook are enabled in `.env`
   - Check backend server is running

2. **"Connector is not connected" messages**
   - Gmail/Outlook credentials may be incorrect
   - Check `.env` configuration
   - Check connection test scripts

3. **"Error fetching emails" messages**
   - Network issues
   - API rate limits
   - Authentication problems

4. **No emails found**
   - May be normal if no emails in the time window
   - Check if emails exist in your inbox
   - Verify lookback window (default: 5 minutes)

## Testing

To verify the system is working:

1. **Send yourself a test email** with high importance
2. **Wait up to 5 minutes** for the next check cycle
3. **Check the logs** for:
   - Email fetch from Gmail/Outlook
   - Email importance check
   - Notification being sent

Or run the test script:
```bash
python3 test_gmail_emails.py  # For Gmail
python3 test_outlook_emails.py  # For Outlook
```

## Log Levels

The logging uses these levels:
- **INFO**: Normal operation (check cycles, fetches, notifications)
- **DEBUG**: Detailed information (individual email details, importance checks)
- **WARNING**: Non-critical issues (connector not connected, etc.)
- **ERROR**: Critical errors (fetch failures, notification errors)

To see DEBUG logs, set log level to DEBUG in `config/config.yaml`:
```yaml
logging:
  level: DEBUG
```

## Real-Time Monitoring

To watch the email monitor in real-time:
```bash
# Follow the log file
tail -f logs/assistant.log | grep -E "EMAIL|📧|📬|🔍|✅|❌|🔔|Gmail|Outlook"
```

This will show only email-related log entries as they happen.

