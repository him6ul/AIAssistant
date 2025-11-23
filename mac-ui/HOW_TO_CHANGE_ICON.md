# How to Change the Menu Bar Icon

The menu bar app currently uses a system SF Symbol (`brain.head.profile`). You can change it to:
1. A different SF Symbol (easiest)
2. A custom icon image file (more control)

## Option 1: Change to a Different SF Symbol (Easiest)

### Step 1: Choose an SF Symbol
Browse available SF Symbols at: https://developer.apple.com/sf-symbols/

Popular choices:
- `brain.head.profile` (current - brain icon)
- `sparkles` (sparkles)
- `star.fill` (filled star)
- `bolt.fill` (lightning bolt)
- `waveform` (sound wave)
- `message.fill` (message bubble)
- `person.circle.fill` (person icon)
- `gearshape.fill` (gear/settings)
- `app.badge` (app icon)
- `command` (command symbol)

### Step 2: Edit MenuBarApp.swift

Open `mac-ui/Sources/MenuBarApp.swift` and find this line (around line 41):

```swift
if let brainImage = NSImage(systemSymbolName: "brain.head.profile", accessibilityDescription: "AI Assistant") {
```

Change `"brain.head.profile"` to your chosen symbol name, for example:

```swift
if let brainImage = NSImage(systemSymbolName: "sparkles", accessibilityDescription: "AI Assistant") {
```

### Step 3: Rebuild the App

1. Open the project in Xcode
2. Press **⌘B** (Build)
3. Press **⌘R** (Run)

The new icon will appear in your menu bar.

## Option 2: Use a Custom Icon Image File

### Step 1: Prepare Your Icon

You need an icon file in one of these formats:
- **.icns** (macOS icon format - recommended)
- **.png** (with transparency)
- **.pdf** (vector format)

**Recommended size:** 20x20 pixels for menu bar (or 40x40 for Retina)

### Step 2: Create .icns File (Optional but Recommended)

If you have a PNG image, convert it to .icns:

1. Open **Terminal**
2. Run:
   ```bash
   # If you have iconutil (built into macOS)
   iconutil -c icns /path/to/your/icon.iconset
   
   # Or use online converter: https://cloudconvert.com/png-to-icns
   ```

Or use a tool like:
- **Icon Composer** (part of Xcode)
- Online converters (search "png to icns converter")

### Step 3: Add Icon to Xcode Project

1. Open the project in **Xcode**
2. Right-click on the project in the navigator
3. Select **"Add Files to [Project Name]"**
4. Select your `.icns` or `.png` file
5. Make sure **"Copy items if needed"** is checked
6. Click **Add**

### Step 4: Update MenuBarApp.swift

Open `mac-ui/Sources/MenuBarApp.swift` and replace the icon loading code:

**Find this section (around lines 38-48):**
```swift
// Try to create icon
var iconImage: NSImage?

if #available(macOS 11.0, *) {
    if let brainImage = NSImage(systemSymbolName: "brain.head.profile", accessibilityDescription: "AI Assistant") {
        iconImage = brainImage
    }
}
```

**Replace with:**
```swift
// Try to load custom icon
var iconImage: NSImage?

// First try to load custom icon from bundle
if let customIcon = NSImage(named: "YourIconName") {
    iconImage = customIcon
}
// Fallback to SF Symbol if custom icon not found
else if #available(macOS 11.0, *) {
    if let brainImage = NSImage(systemSymbolName: "brain.head.profile", accessibilityDescription: "AI Assistant") {
        iconImage = brainImage
    }
}
```

**Important:** Replace `"YourIconName"` with the actual name of your icon file (without extension).

For example, if your file is `assistant-icon.icns`, use:
```swift
if let customIcon = NSImage(named: "assistant-icon") {
    iconImage = customIcon
}
```

### Step 5: Rebuild the App

1. In Xcode, press **⌘B** (Build)
2. Press **⌘R** (Run)

## Option 3: Use Emoji as Icon (Simple Fallback)

If you want a quick change without rebuilding, the app already has a fallback that shows a 🧠 emoji if the icon fails to load. You can modify the code to always use an emoji:

**In MenuBarApp.swift, replace the icon section with:**
```swift
// Use emoji as icon
button.title = "🧠"  // or any emoji you prefer: ⚡️, ✨, 🤖, 💬, etc.
button.imagePosition = .noImage
```

Popular emoji choices:
- 🧠 (brain - current)
- ⚡️ (lightning)
- ✨ (sparkles)
- 🤖 (robot)
- 💬 (speech bubble)
- ⭐️ (star)
- 🎯 (target)
- 🔮 (crystal ball)

## Quick Reference: Icon Sizes

- **Menu bar icon:** 20x20 pixels (or 40x40 for Retina)
- **App icon:** 512x512 pixels (for full app icon if needed)

## Troubleshooting

### Icon Not Showing
1. Make sure the icon file is added to the Xcode project
2. Check that the file name in code matches the actual file name (case-sensitive)
3. Verify the icon file is included in the app bundle (check Build Phases > Copy Bundle Resources)
4. Try cleaning the build folder: **⇧⌘K** (Shift+Command+K)

### Icon Looks Blurry
- Use a higher resolution image (40x40 for Retina displays)
- Use vector format (.pdf) if possible
- Make sure the image has proper transparency

### Want to Change Icon Color
SF Symbols automatically adapt to your macOS appearance (light/dark mode). For custom icons:
- Use a template image (set `icon.isTemplate = true`)
- The icon will be tinted to match the menu bar appearance

## Example: Complete Custom Icon Implementation

Here's a complete example that tries custom icon first, then SF Symbol, then emoji:

```swift
// Try to create icon
var iconImage: NSImage?

// 1. Try custom icon from bundle
if let customIcon = NSImage(named: "assistant-icon") {
    iconImage = customIcon
}
// 2. Fallback to SF Symbol
else if #available(macOS 11.0, *) {
    if let symbolIcon = NSImage(systemSymbolName: "sparkles", accessibilityDescription: "AI Assistant") {
        iconImage = symbolIcon
    }
}
// 3. Fallback to gear icon
if iconImage == nil {
    if let gearImage = NSImage(systemSymbolName: "gearshape.fill", accessibilityDescription: "AI Assistant") {
        iconImage = gearImage
    }
}

if let icon = iconImage {
    icon.isTemplate = true
    icon.size = NSSize(width: 20, height: 20)
    button.image = icon
    button.imagePosition = .imageOnly
} else {
    // Final fallback: emoji
    button.title = "🧠"
    button.imagePosition = .noImage
}
```

## Need Help?

- Browse SF Symbols: https://developer.apple.com/sf-symbols/
- Icon design tools: https://www.iconfinder.com/ or create your own
- Convert images: https://cloudconvert.com/ (supports many formats)

