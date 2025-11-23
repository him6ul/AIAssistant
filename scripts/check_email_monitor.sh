#!/bin/bash
# Quick status check for email monitoring

LOG_FILE="logs/assistant.log"

echo "📊 Email Monitor Status Check"
echo "=============================="
echo ""

# Check if log file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "   Make sure the backend server is running"
    exit 1
fi

# Check if monitor started
if grep -q "STARTING EMAIL NOTIFICATION MONITOR" "$LOG_FILE"; then
    echo "✅ Monitor is running"
    LAST_START=$(grep "STARTING EMAIL NOTIFICATION MONITOR" "$LOG_FILE" | tail -1 | sed 's/.*| //')
    echo "   Last start: $LAST_START"
else
    echo "❌ Monitor has not started"
    echo "   Check if Gmail/Outlook are enabled in .env"
fi

echo ""

# Count check cycles
CHECK_COUNT=$(grep -c "EMAIL MONITOR CHECK STARTED" "$LOG_FILE" 2>/dev/null || echo "0")
echo "📧 Total check cycles: $CHECK_COUNT"

# Last check time
LAST_CHECK=$(grep "EMAIL MONITOR CHECK STARTED" "$LOG_FILE" | tail -1)
if [ -n "$LAST_CHECK" ]; then
    LAST_CHECK_TIME=$(echo "$LAST_CHECK" | grep -oP '\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}' | head -1)
    echo "   Last check: $LAST_CHECK_TIME"
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
echo "View email activity: tail -f $LOG_FILE | grep -E 'EMAIL|📧|📬|🔍|✅|❌|🔔'"

