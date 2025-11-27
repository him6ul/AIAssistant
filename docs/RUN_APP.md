# How to Run the AI Assistant App

## Quick Start (3 Steps)

### Step 1: Start the Backend Server
```bash
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
./scripts/run_backend.sh
```

The backend will start on `http://localhost:8000`

### Step 2: Run the Menu Bar App

**Option A: From Xcode (Recommended)**
```bash
cd mac-ui
open Package.swift
```

Then in Xcode:
1. Wait for package resolution
2. Select "MenuBarApp" scheme (top left)
3. Select "My Mac" as destination
4. Press **⌘R** (or click Play button)

**Option B: Run the Built App Directly**
```bash
# The app is already built at:
~/Library/Developer/Xcode/DerivedData/mac-ui-ckrmxprzbezrhgaxmgfdbywntpen/Build/Products/Debug/MenuBarApp

# Run it:
~/Library/Developer/Xcode/DerivedData/mac-ui-ckrmxprzbezrhgaxmgfdbywntpen/Build/Products/Debug/MenuBarApp
```

### Step 3: Find the Icon
- Look in the **top-right corner** of your screen (menu bar)
- The brain icon 🧠 should appear near the clock
- Click it to open the interface

---

## Complete Run Script

I can create a simple script to run everything:

```bash
# Run both backend and menu bar app
cd /Users/himanshu/SourceCode/Personal/AI_Assistant
./scripts/run_all.sh
```

---

## Troubleshooting

### Backend not starting?
- Check if port 8000 is in use: `lsof -ti:8000`
- Check logs: Look for errors in terminal
- Make sure dependencies are installed: `pip install -r requirements.txt`

### Menu bar app not appearing?
- Check if it's running: `ps aux | grep MenuBarApp`
- Check Xcode console for errors
- Try rebuilding: In Xcode, press **⇧⌘K** then **⌘B**

### Connection errors?
- Verify backend is running: `curl http://localhost:8000/health`
- Should return: `{"status":"healthy","network":"online"}`

---

## What You'll See

1. **Backend running**: Terminal shows "Uvicorn running on http://localhost:8000"
2. **Menu bar icon**: Brain icon 🧠 appears in top-right menu bar
3. **Click icon**: Opens popover with Chat and Tasks tabs
4. **Status indicator**: Shows if backend is online/offline

---

## Stop the App

- **Backend**: Press `Ctrl+C` in the terminal
- **Menu bar app**: Right-click the icon → Quit, or:
  ```bash
  killall MenuBarApp
  ```

