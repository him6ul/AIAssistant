# Quick Start Guide

## ✅ Your Xcode Project is Ready!

The project is set up as a **Swift Package**, which is the modern and recommended approach.

## 🚀 Open in Xcode (3 Ways)

### Method 1: Open Package.swift (Easiest)
```bash
cd mac-ui
open Package.swift
```

### Method 2: Use the Setup Script
```bash
cd mac-ui
./setup_xcode.sh
```

### Method 3: From Xcode
1. Open Xcode
2. File > Open
3. Navigate to `mac-ui/Package.swift`
4. Click Open

## 📱 Build and Run

Once Xcode opens:

1. **Wait for package resolution** (Xcode will do this automatically)
2. **Select scheme**: Choose "MenuBarApp" from the scheme dropdown (top left)
3. **Select destination**: Choose "My Mac" 
4. **Build and Run**: Press **⌘R** or click the Play button ▶️

## 🎯 What to Expect

- The app will build successfully ✅
- The app will launch and appear in your **menu bar** (top right of screen)
- You'll see a **brain icon** 🧠
- **Click the icon** to open the chat/task interface

## 🔧 Configuration

### Hide from Dock
The app is configured to run as a menu bar app (hidden from Dock). This is set in the code via `LSUIElement`.

### Backend Connection
Make sure your backend is running:
```bash
cd ..
./scripts/run_backend.sh
```

The app connects to: `http://localhost:8000`

## 🐛 Troubleshooting

### "Cannot build" or "Package resolution failed"
- Make sure you have Xcode 14+ installed
- Try: File > Packages > Reset Package Caches
- Clean build: Product > Clean Build Folder (⇧⌘K)

### App doesn't appear in menu bar
- Check Console for errors (View > Debug Area > Show Debug Area)
- Make sure the app is actually running
- Try restarting the app

### Connection errors
- Verify backend is running: `curl http://localhost:8000/health`
- Check API URL in `APIClient.swift`
- Ensure CORS is enabled in backend

## 📁 Project Structure

```
mac-ui/
├── Package.swift          ← Open this in Xcode!
├── Sources/              ← All your Swift code
│   ├── MenuBarApp.swift ← Main entry point
│   ├── ChatView.swift   ← Chat interface
│   ├── TaskViews.swift  ← Task management
│   └── APIClient.swift  ← API communication
└── setup_xcode.sh       ← Helper script
```

## ✨ Features

- ✅ Menu bar app (no Dock icon)
- ✅ Chat interface with AI
- ✅ Task management (Today, Overdue, Waiting On, Follow-ups)
- ✅ Quick actions (Email scan, OneNote scan)
- ✅ Status indicator (Online/Offline mode)
- ✅ Real-time API communication

## 🎨 Customization

Edit the Swift files in `Sources/` to customize:
- UI appearance
- Colors and styling
- API endpoints
- Features and functionality

## 📚 More Help

See `XCODE_SETUP.md` for detailed setup instructions.

---

**Ready to go?** Just run: `cd mac-ui && open Package.swift` 🚀

