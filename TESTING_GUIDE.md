# Testing Guide - AI Personal Assistant

## ✅ System Status: READY

Both services are running:
- ✅ Backend API: `http://localhost:8000`
- ✅ Menu Bar App: Running

---

## 🧪 Testing Methods

### Method 1: Test via Menu Bar App (UI Testing)

1. **Find the Menu Bar Icon**
   - Look in the **top-right corner** of your screen
   - Find the brain icon 🧠 in the menu bar
   - If you don't see it, check Activity Monitor for "MenuBarApp"

2. **Click the Icon**
   - Click the brain icon to open the popover
   - You should see two tabs: **Chat** and **Tasks**

3. **Test Chat Interface**
   - Go to the **Chat** tab
   - Type a message like: "Hello, what can you help me with?"
   - Press Enter or click Send
   - You should see a response from the AI

4. **Test Tasks Interface**
   - Go to the **Tasks** tab
   - You should see task categories:
     - Today
     - Overdue
     - Waiting On
     - Follow-ups
   - Try clicking "Scan Emails" or "Scan OneNote" buttons

5. **Check Status Indicator**
   - Look at the top-right of the popover
   - Should show: Green dot (online) or Orange dot (offline)
   - Should show the LLM mode (e.g., "openai", "ollama")

---

### Method 2: Test via API (Command Line)

#### 1. Health Check
```bash
curl http://localhost:8000/health
```
**Expected:** `{"status":"healthy","network":"online"}`

#### 2. Get System Status
```bash
curl http://localhost:8000/status
```
**Expected:** Status with network and LLM mode

#### 3. Test Chat Endpoint
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, what can you help me with?"}'
```
**Expected:** JSON response with AI reply

#### 4. Get Tasks
```bash
curl http://localhost:8000/tasks
```
**Expected:** Array of tasks (may be empty initially)

#### 5. Create a Task
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "This is a test task",
    "importance": "medium",
    "classification": "do"
  }'
```
**Expected:** Created task object

#### 6. Get Tasks by Status
```bash
# Get today's tasks
curl "http://localhost:8000/tasks?status=active"

# Get overdue tasks
curl "http://localhost:8000/tasks?overdue=true"
```

#### 7. Test Email Scan
```bash
curl -X POST http://localhost:8000/ingestion/email/scan
```
**Expected:** Scan result (may show 0 if no emails or credentials not configured)

#### 8. Test OneNote Scan
```bash
curl -X POST http://localhost:8000/ingestion/onenote/scan
```
**Expected:** Scan result (may show 0 if no pages or credentials not configured)

---

### Method 3: Test via Browser

1. **Open API Documentation**
   - Go to: `http://localhost:8000/docs`
   - This opens Swagger UI with all available endpoints
   - You can test endpoints directly from the browser

2. **Test Endpoints**
   - Click on any endpoint (e.g., `/health`)
   - Click "Try it out"
   - Click "Execute"
   - See the response

---

## 📋 Complete Test Checklist

### Backend API Tests
- [ ] Health check returns healthy
- [ ] Status endpoint returns network and LLM mode
- [ ] Chat endpoint responds to messages
- [ ] Tasks endpoint returns task list
- [ ] Can create a new task
- [ ] Can update a task
- [ ] Can delete a task
- [ ] Can filter tasks by status/classification
- [ ] Email scan endpoint works (may return 0)
- [ ] OneNote scan endpoint works (may return 0)

### Menu Bar App Tests
- [ ] App icon appears in menu bar
- [ ] Clicking icon opens popover
- [ ] Chat tab displays correctly
- [ ] Can send messages in chat
- [ ] Receive responses from AI
- [ ] Tasks tab displays correctly
- [ ] Task categories show (Today, Overdue, etc.)
- [ ] Status indicator shows online/offline
- [ ] Status indicator shows LLM mode
- [ ] Scan buttons are clickable
- [ ] App stays running in background

### Integration Tests
- [ ] Menu bar app connects to backend
- [ ] Status updates reflect backend state
- [ ] Tasks sync between API and UI
- [ ] Chat messages are sent to backend
- [ ] Responses are displayed in UI

---

## 🐛 Troubleshooting Tests

### Backend Not Responding?
```bash
# Check if backend is running
ps aux | grep "python.*app.main"

# Check if port is in use
lsof -ti:8000

# Restart backend
./scripts/run_backend.sh
```

### Menu Bar App Not Visible?
```bash
# Check if app is running
ps aux | grep MenuBarApp

# Restart app
killall MenuBarApp
cd mac-ui && open Package.swift
# Then press ⌘R in Xcode
```

### API Errors?
- Check backend logs in terminal
- Verify CORS is enabled (should be `allow_origins=["*"]`)
- Check if LLM credentials are configured (for chat to work)

### Chat Not Working?
- Verify LLM router is configured
- Check if OpenAI API key is set (if using OpenAI)
- Check if Ollama is running (if using Ollama)
- Look at backend logs for errors

---

## 🎯 Quick Test Script

Run this to test all endpoints:

```bash
#!/bin/bash

echo "Testing AI Assistant API..."
echo ""

echo "1. Health Check:"
curl -s http://localhost:8000/health | jq .
echo ""

echo "2. Status:"
curl -s http://localhost:8000/status | jq .
echo ""

echo "3. Chat Test:"
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}' | jq .
echo ""

echo "4. Get Tasks:"
curl -s http://localhost:8000/tasks | jq .
echo ""

echo "✅ Tests complete!"
```

Save as `test_api.sh`, make executable, and run:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## 📊 Expected Results

### Healthy System Should Show:
- ✅ Backend responds to `/health` with `{"status":"healthy"}`
- ✅ Status shows network as "online"
- ✅ Menu bar icon is visible
- ✅ Chat interface loads
- ✅ Tasks interface loads
- ✅ Can send/receive chat messages
- ✅ Tasks can be created and viewed

### Known Limitations (Not Errors):
- ⚠️ Email/OneNote scan may return 0 if credentials not configured
- ⚠️ Chat may not work if LLM credentials not set
- ⚠️ Some features require Microsoft Graph API credentials

---

## 🚀 Next Steps After Testing

1. **Configure LLM** (for chat to work):
   - Set `OPENAI_API_KEY` environment variable, or
   - Install and run Ollama locally

2. **Configure Email/OneNote** (optional):
   - Set Microsoft Graph API credentials
   - See `config/credentials.example.yaml`

3. **Customize UI**:
   - Edit `mac-ui/Sources/ChatView.swift`
   - Edit `mac-ui/Sources/TaskViews.swift`

4. **Add Auto-Start**:
   - Run `mac-ui/setup_auto_start.sh` to start on login

---

**Ready to test? Start with the health check:**
```bash
curl http://localhost:8000/health
```

