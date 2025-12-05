#!/usr/bin/env python3
"""
Run this script after saving screenshots to ensure thumbnails are generated.
This ensures thumbnails are always created for new screenshots.
"""
import subprocess
import sys

if __name__ == "__main__":
    # Run thumbnail generation
    result = subprocess.run([sys.executable, "create_thumbnails.py"], 
                          capture_output=True, text=True)
    
    # Only show errors, not the full output
    if result.returncode != 0:
        print("Error generating thumbnails:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    
    # Check if any thumbnails were created
    if "Thumbnails created/updated: 0" not in result.stdout:
        print("✓ Thumbnails generated successfully")












