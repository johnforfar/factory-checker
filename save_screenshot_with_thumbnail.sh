#!/bin/bash
# Save screenshot and automatically generate thumbnail
# Usage: ./save_screenshot_with_thumbnail.sh app_name temp_path

APP_NAME=$1
TEMP_PATH=$2
APPS_DIR="app-review/public/apps"
APP_DIR="$APPS_DIR/$APP_NAME"

# Create app directory
mkdir -p "$APP_DIR"

# Copy screenshot
if [ -f "$TEMP_PATH" ]; then
    cp "$TEMP_PATH" "$APP_DIR/screenshot-1.png"
    echo "Saved screenshot for $APP_NAME"
    
    # Generate thumbnail automatically
    python3 create_thumbnails.py > /dev/null 2>&1
    echo "Generated thumbnail for $APP_NAME"
else
    echo "Error: Screenshot file not found: $TEMP_PATH"
    exit 1
fi












