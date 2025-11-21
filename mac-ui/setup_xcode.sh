#!/bin/bash

# Setup script for Xcode project
# This will open the Swift Package in Xcode

cd "$(dirname "$0")"

echo "🚀 Setting up Xcode project for MenuBarApp"
echo ""

# Check if Xcode is installed
if ! command -v xcodebuild &> /dev/null; then
    echo "❌ Xcode is not installed. Please install Xcode from the App Store."
    exit 1
fi

echo "✅ Xcode found"
echo ""

# Open Package.swift in Xcode
echo "Opening Package.swift in Xcode..."
open Package.swift

echo ""
echo "✅ Xcode should now be opening..."
echo ""
echo "📋 Next steps in Xcode:"
echo "1. Wait for Xcode to resolve the package"
echo "2. Select the 'MenuBarApp' scheme from the scheme selector"
echo "3. Choose 'My Mac' as the destination"
echo "4. Press ⌘R to build and run"
echo ""
echo "💡 Tips:"
echo "- The app will appear in your menu bar when running"
echo "- Make sure the backend server is running on localhost:8000"
echo "- Check the console for any connection errors"
echo ""

