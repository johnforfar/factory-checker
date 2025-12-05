#!/usr/bin/env python3
"""
Process all remaining screenshots continuously until complete.
This script will process apps in batches and keep going until all are done.
"""
import json
import os
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def get_all_apps_needing_screenshots(include_pending=True):
    """
    Get all apps needing screenshots.
    By default includes ALL apps (Pending, Active, Default).
    """
    state = load_state()
    needs_screenshots = []
    
    for name, data in state.items():
        status = data.get('status', 'Pending')
        
        # Skip Pending if not including them
        if not include_pending and status == 'Pending':
            continue
        
        app_path = os.path.join(APPS_DIR, name)
        screenshots = []
        
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
        
        if len(screenshots) == 0:
            url = f"https://{name}.miniapp-factory.marketplace.openxai.network"
            needs_screenshots.append((name, url, status))
    
    return needs_screenshots

def save_screenshot(app_name, screenshot_path):
    """Save screenshot to the app directory"""
    app_dir = os.path.join(APPS_DIR, app_name)
    os.makedirs(app_dir, exist_ok=True)
    
    dest_path = os.path.join(app_dir, "screenshot-1.png")
    if os.path.exists(screenshot_path):
        subprocess.run(["cp", screenshot_path, dest_path], check=False)
        return os.path.exists(dest_path)
    return False

if __name__ == "__main__":
    import sys
    
    include_pending = not ('--no-pending' in sys.argv)
    apps = get_all_apps_needing_screenshots(include_pending=include_pending)
    total = len(apps)
    
    print(f"\n{'='*70}")
    print(f"PROCESSING ALL REMAINING SCREENSHOTS")
    print(f"Total apps needing screenshots: {total}")
    if include_pending:
        print(f"(Including Pending, Active, and Default apps)")
    else:
        print(f"(Active and Default apps only)")
    print(f"{'='*70}\n")
    
    if total == 0:
        print("✅ All apps already have screenshots!")
        exit(0)
    
    print(f"Starting batch processing...")
    print(f"This will process apps in batches and continue until all {total} are complete.\n")
    
    # Show first batch
    print(f"First 30 apps:\n")
    for i, (name, url, status) in enumerate(apps[:30], 1):
        print(f"{i:3d}. [{status:8s}] {name:35s} -> {url}")
    if total > 30:
        print(f"\n... and {total - 30} more apps")


