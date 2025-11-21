#!/bin/bash

# Setup script to add MenuBarApp to auto-start on login

echo "🚀 Setting up MenuBarApp to start automatically on login..."
echo ""

# Find the app in DerivedData
APP_PATH=$(find ~/Library/Developer/Xcode/DerivedData -name "MenuBarApp" -type f -path "*/Build/Products/*/MenuBarApp" 2>/dev/null | head -1)

if [ -z "$APP_PATH" ]; then
    echo "❌ MenuBarApp not found in DerivedData"
    echo ""
    echo "Please:"
    echo "1. Build and run the app once from Xcode (⌘R)"
    echo "2. Then run this script again"
    exit 1
fi

echo "✅ Found MenuBarApp at: $APP_PATH"
echo ""

# Method 1: Add to Login Items using osascript
echo "Adding to Login Items..."
osascript <<EOF
tell application "System Events"
    -- Get the login items
    set loginItems to login items
    
    -- Check if already added
    set appName to name of (info for "$APP_PATH")
    set alreadyAdded to false
    repeat with item in loginItems
        if name of item is appName then
            set alreadyAdded to true
            exit repeat
        end if
    end repeat
    
    if not alreadyAdded then
        -- Add to login items
        make login item at end with properties {path:"$APP_PATH", hidden:false}
        display notification "MenuBarApp added to Login Items" with title "Auto-Start Setup"
        return "✅ Added to Login Items successfully!"
    else
        return "ℹ️  Already in Login Items"
    end if
end tell
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Log out and log back in, or restart your Mac"
echo "2. MenuBarApp should start automatically"
echo ""
echo "💡 To remove auto-start:"
echo "   System Settings → General → Login Items → Remove MenuBarApp"

