# Xcode Project Setup Guide

## Quick Start (Recommended)

The easiest way is to open the Swift Package directly in Xcode:

```bash
cd mac-ui
open Package.swift
```

Xcode will automatically:
- Create the project structure
- Resolve dependencies
- Set up the build system

Then:
1. Select the "MenuBarApp" scheme
2. Choose "My Mac" as destination
3. Press ⌘R to build and run

## Alternative: Create New Xcode Project

If you prefer a traditional Xcode project:

### Step 1: Create New Project
1. Open Xcode
2. File > New > Project
3. Choose **macOS** > **App**
4. Click Next

### Step 2: Configure Project
- **Product Name**: `MenuBarApp`
- **Team**: Select your development team
- **Organization Identifier**: `com.aipersonalassistant` (or your own)
- **Interface**: **SwiftUI**
- **Language**: **Swift**
- **Storage**: None (or Core Data if you want)
- **Include Tests**: Optional

### Step 3: Save Location
- Save in: `mac-ui/` directory
- **Important**: Choose "Create Git repository" if you want, or uncheck it

### Step 4: Replace Generated Files
1. Delete the auto-generated `MenuBarAppApp.swift` (or `App.swift`)
2. Copy all files from `Sources/` into your project:
   - `MenuBarApp.swift`
   - `ChatView.swift`
   - `TaskViews.swift`
   - `APIClient.swift`

### Step 5: Configure Info.plist
1. Select your project in the navigator
2. Go to **Info** tab
3. Add key: **Application is agent (UIElement)** = **YES**
   - This hides the app from the Dock

Or edit `Info.plist` directly:
```xml
<key>LSUIElement</key>
<true/>
```

### Step 6: Build Settings
1. Select your project
2. Go to **Build Settings**
3. Set **Minimum macOS Deployment Target** to **12.0** or higher

### Step 7: Signing & Capabilities
1. Select your target
2. Go to **Signing & Capabilities**
3. Select your **Team**
4. Enable **App Sandbox** (optional)
5. Add **Outgoing Connections (Client)** capability

## Build and Run

1. Select **MenuBarApp** scheme
2. Choose **My Mac** as destination
3. Press **⌘R** or click the Play button

The app will:
- Build and launch
- Appear in your menu bar (top right)
- Show a brain icon
- Click to open the interface

## Troubleshooting

### "Cannot find 'APIClient' in scope"
- Make sure all Swift files are added to the target
- Check Target Membership in File Inspector

### App doesn't appear in menu bar
- Check Console for errors
- Verify `LSUIElement` is set to `YES` in Info.plist
- Make sure the app is actually running (check Activity Monitor)

### Connection errors
- Ensure backend server is running: `./scripts/run_backend.sh`
- Check API URL in `APIClient.swift` (should be `http://localhost:8000`)
- Verify CORS is enabled in backend

### Build errors
- Clean build folder: **Product > Clean Build Folder** (⇧⌘K)
- Delete Derived Data
- Restart Xcode

## Project Structure

```
mac-ui/
├── Package.swift          # Swift Package manifest
├── Sources/               # Source files
│   ├── MenuBarApp.swift  # Main app entry
│   ├── ChatView.swift    # Chat interface
│   ├── TaskViews.swift   # Task management
│   └── APIClient.swift   # API client
├── Info.plist            # App configuration
└── XCODE_SETUP.md        # This file
```

## Using Swift Package Manager (Current Setup)

The project is set up as a Swift Package, which is the modern approach:

**Advantages:**
- No complex Xcode project file to manage
- Easy to version control
- Works with Xcode and command line
- Automatic dependency resolution

**To use:**
```bash
cd mac-ui
open Package.swift  # Opens in Xcode
# OR
swift build         # Build from command line
swift run           # Run from command line
```

## Next Steps

1. ✅ Open project in Xcode
2. ✅ Build and run
3. ✅ Test menu bar functionality
4. ✅ Connect to backend API
5. ✅ Customize UI as needed

