# Auto-Start MenuBarApp on Login

There are two ways to make MenuBarApp start automatically when you log in:

## Method 1: System Settings (Easiest) ✅

1. **Build and run the app once** from Xcode to create the app bundle
2. **Find the app location:**
   - The built app is usually at:
     ```
     ~/Library/Developer/Xcode/DerivedData/mac-ui-*/Build/Products/Debug/MenuBarApp
     ```
   - Or you can find it by:
     - Opening Finder
     - Press ⌘⇧G (Go to Folder)
     - Type: `~/Library/Developer/Xcode/DerivedData`
     - Look for folders starting with `mac-ui-`
     - Navigate to `Build/Products/Debug/`
     - Find `MenuBarApp`

3. **Add to Login Items:**
   - Open **System Settings** (or System Preferences on older macOS)
   - Go to **General** → **Login Items** (or **Users & Groups** → **Login Items** on older macOS)
   - Click the **+** button
   - Navigate to the MenuBarApp location and select it
   - Make sure the checkbox next to it is **checked**
   - The app will now start automatically when you log in

## Method 2: Launch Agent (More Control)

This method uses a Launch Agent plist file for more control.

### Steps:

1. **Find the app path** (same as Method 1)

2. **Create a Launch Agent plist:**
   ```bash
   # Run the setup script
   cd mac-ui
   ./setup_auto_start.sh
   ```

3. **Or manually create the plist:**
   - Create file: `~/Library/LaunchAgents/com.aipersonalassistant.menubarapp.plist`
   - Add the content (see below)

4. **Load the Launch Agent:**
   ```bash
   launchctl load ~/Library/LaunchAgents/com.aipersonalassistant.menubarapp.plist
   ```

## Method 3: Copy App to Applications (Recommended for Production)

For a more permanent solution:

1. **Build the app in Release mode:**
   - In Xcode: Product → Scheme → Edit Scheme
   - Set Build Configuration to **Release**
   - Build (⌘B)

2. **Copy to Applications:**
   ```bash
   # Find the Release build
   # Usually at: ~/Library/Developer/Xcode/DerivedData/mac-ui-*/Build/Products/Release/MenuBarApp.app
   
   # Copy to Applications
   cp -R ~/Library/Developer/Xcode/DerivedData/mac-ui-*/Build/Products/Release/MenuBarApp.app /Applications/
   ```

3. **Add to Login Items:**
   - System Settings → General → Login Items
   - Click **+** and select `/Applications/MenuBarApp.app`

## Verify It Works

1. **Log out and log back in**, or
2. **Restart your Mac**
3. The MenuBarApp should appear in your menu bar automatically

## Remove Auto-Start

### If using Login Items:
- System Settings → General → Login Items
- Select MenuBarApp and click **-** (minus button)

### If using Launch Agent:
```bash
launchctl unload ~/Library/LaunchAgents/com.aipersonalassistant.menubarapp.plist
rm ~/Library/LaunchAgents/com.aipersonalassistant.menubarapp.plist
```

