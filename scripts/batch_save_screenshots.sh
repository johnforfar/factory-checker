#!/bin/bash
# Batch save screenshots from temp directory to app directories

TEMP_DIR="/var/folders/bn/ml8l4wps6770plhr2r14g0dm0000gn/T/cursor/screenshots"
APPS_DIR="app-review/public/apps"

# Process all screenshots in temp directory
for screenshot in "$TEMP_DIR"/*-screenshot.png; do
    if [ -f "$screenshot" ]; then
        filename=$(basename "$screenshot")
        # Extract app name (remove -screenshot.png suffix)
        app_name=$(echo "$filename" | sed 's/-screenshot\.png$//')
        
        # Create app directory if it doesn't exist
        mkdir -p "$APPS_DIR/$app_name"
        
        # Copy screenshot
        cp "$screenshot" "$APPS_DIR/$app_name/screenshot-1.png"
        echo "Saved screenshot for: $app_name"
    fi
done

echo "Done!"












