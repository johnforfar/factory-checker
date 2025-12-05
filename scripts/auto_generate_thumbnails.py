#!/usr/bin/env python3
"""
Automatically generate thumbnails for newly added screenshots.
This script should be run after screenshots are saved to ensure thumbnails exist.
"""
import subprocess
import sys

if __name__ == "__main__":
    # Run the thumbnail generation script
    result = subprocess.run([sys.executable, "create_thumbnails.py"], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    sys.exit(result.returncode)












