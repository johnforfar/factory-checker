#!/usr/bin/env python3
"""
Automated screenshot processor using browser automation.
This script processes apps in batches, taking screenshots and updating state.
"""
import json
import os
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_apps_needing_screenshots(include_pending=True):
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

def is_app_complete(data, app_path):
    """Check if an app has all required data for completion (including Pending apps)"""
    has_github = data.get('last_updated') and data.get('last_updated') != 'Never' and data.get('last_updated') != 'Unknown'
    
    has_icon = False
    has_screenshot = False
    if os.path.exists(app_path):
        files = os.listdir(app_path)
        has_icon = any('icon' in f.lower() or 'logo' in f.lower() for f in files if f.endswith('.png'))
        screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
        has_screenshot = len(screenshots) > 0
    
    return has_github and has_icon and has_screenshot

def update_last_checked_for_complete_apps(promote_pending=True):
    """
    Update last_checked for apps that have all required data.
    Also promotes Pending apps to Active when they become complete.
    """
    state = load_state()
    updated_count = 0
    promoted_count = 0
    now = datetime.now().isoformat()
    
    for name, data in state.items():
        app_path = os.path.join(APPS_DIR, name)
        if is_app_complete(data, app_path):
            # Promote Pending to Active if requested
            if promote_pending and data.get('status') == 'Pending':
                data['status'] = 'Active'
                promoted_count += 1
            
            # Update last_checked if not set or if it's Never
            if not data.get('last_checked') or data.get('last_checked') == 'Never':
                data['last_checked'] = now
                updated_count += 1
    
    save_state(state)
    if promoted_count > 0:
        print(f"Promoted {promoted_count} Pending apps to Active")
    return updated_count

if __name__ == "__main__":
    import sys
    
    include_pending = not ('--no-pending' in sys.argv)
    apps = get_apps_needing_screenshots(include_pending=include_pending)
    total = len(apps)
    
    print(f"\n{'='*70}")
    print(f"AUTOMATED SCREENSHOT PROCESSOR")
    print(f"Total apps needing screenshots: {total}")
    if include_pending:
        print(f"(Including Pending, Active, and Default apps)")
    else:
        print(f"(Active and Default apps only)")
    print(f"{'='*70}\n")
    
    if total == 0:
        print("✅ All apps already have screenshots!")
        # Update last_checked for any newly complete apps
        promote = not ('--no-promote' in sys.argv)
        updated = update_last_checked_for_complete_apps(promote_pending=promote)
        if updated > 0:
            print(f"Updated last_checked for {updated} apps")
        exit(0)
    
    print(f"This script will process apps in batches.")
    print(f"Each batch will be processed automatically.\n")
    print(f"Apps to process:\n")
    for i, (name, url, status) in enumerate(apps[:50], 1):
        print(f"{i:3d}. [{status:8s}] {name:35s} -> {url}")
    if total > 50:
        print(f"\n... and {total - 50} more apps")
    
    print(f"\n{'='*70}")
    print(f"Ready to process {total} apps")
    print(f"{'='*70}\n")

