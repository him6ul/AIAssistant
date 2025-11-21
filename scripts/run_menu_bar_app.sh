#!/bin/bash

# Script to run the MenuBarApp directly

cd "$(dirname "$0")/.."

echo "🚀 Starting MenuBarApp..."
echo ""

# Find the built app
APP_PATH=$(find ~/Library/Developer/Xcode/DerivedData -name "MenuBarApp" -type f -path "*/Build/Products/*/MenuBarApp" 2>/dev/null | head -1)

if [ -z "$APP_PATH" ]; then
    echo "❌ MenuBarApp not found. Building from Xcode first..."
    echo ""
    echo "Please:"
    echo "1. Open Xcode: cd mac-ui && open Package.swift"
    echo "2. Build the app: Press ⌘B"
    echo "3. Run this script again"
    exit 1
fi

echo "✅ Found MenuBarApp at: $APP_PATH"
echo ""
echo "Starting app..."
echo ""

# Run the app
"$APP_PATH" &

echo "✅ MenuBarApp started!"
echo ""
echo "📋 Look for the brain icon 🧠 in your menu bar (top-right corner)"
echo ""
echo "💡 To stop: killall MenuBarApp"

