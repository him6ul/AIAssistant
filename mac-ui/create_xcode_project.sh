#!/bin/bash

# Script to create Xcode project for MenuBarApp
# Run this script to generate the Xcode project

cd "$(dirname "$0")"

PROJECT_NAME="MenuBarApp"
BUNDLE_ID="com.aipersonalassistant.menubarapp"

echo "Creating Xcode project: $PROJECT_NAME"

# Create project directory structure
mkdir -p "$PROJECT_NAME.xcodeproj/project.xcworkspace/xcshareddata"
mkdir -p "$PROJECT_NAME.xcodeproj/xcshareddata/xcschemes"

# Create workspace settings
cat > "$PROJECT_NAME.xcodeproj/project.xcworkspace/contents.xcworkspacedata" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<Workspace
   version = "1.0">
   <FileRef
      location = "self:">
   </FileRef>
</Workspace>
EOF

echo "✅ Xcode project structure created"
echo ""
echo "To complete setup:"
echo "1. Open Xcode"
echo "2. File > New > Project"
echo "3. Choose 'macOS' > 'App'"
echo "4. Product Name: MenuBarApp"
echo "5. Interface: SwiftUI"
echo "6. Language: Swift"
echo "7. Save in: $(pwd)"
echo "8. Replace the generated files with the ones in Sources/"
echo ""
echo "OR use Swift Package Manager:"
echo "  cd mac-ui && swift package generate-xcodeproj"
echo ""
echo "OR open the Package.swift directly in Xcode:"
echo "  open Package.swift"

