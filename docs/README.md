# Menu Bar App Setup

## Creating the Xcode Project

1. **Open Xcode** and create a new project:
   - File > New > Project
   - Select "macOS" > "App"
   - Product Name: `MenuBarApp`
   - Interface: SwiftUI
   - Language: Swift
   - Uncheck "Use Core Data"
   - Save in the `mac-ui/` directory

2. **Configure the App**:
   - In `MenuBarAppApp.swift`, replace with the code from `Sources/MenuBarApp.swift`
   - Add the other Swift files from `Sources/` to the project
   - Ensure "Copy items if needed" is checked

3. **Configure Info.plist**:
   - Add `LSUIElement` = `YES` to hide dock icon
   - Or add to target's Info tab: "Application is agent (UIElement)" = YES

4. **Build Settings**:
   - Minimum macOS version: 12.0
   - Swift version: 5.5+

5. **Signing & Capabilities**:
   - Select your development team
   - Enable "App Sandbox" if needed
   - Add "Outgoing Connections" capability

## Project Structure

```
MenuBarApp.xcodeproj/
├── Sources/
│   ├── MenuBarApp.swift      # Main app entry
│   ├── ChatView.swift        # Chat interface
│   ├── TaskViews.swift       # Task management
│   └── APIClient.swift       # API client
```

## Running the App

1. Build and run from Xcode (⌘R)
2. The app will appear in your menu bar
3. Click the icon to open the interface

## Alternative: Swift Package Manager

If you prefer SPM, create a `Package.swift`:

```swift
// swift-tools-version: 5.5
import PackageDescription

let package = Package(
    name: "MenuBarApp",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(name: "MenuBarApp", targets: ["MenuBarApp"])
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "MenuBarApp",
            dependencies: []
        )
    ]
)
```

Then run: `swift run MenuBarApp`

