#!/usr/bin/env python3
"""
Batch screenshot processor - updates state file after screenshots are taken.
Run this after taking screenshots to update last_checked timestamps.
"""
import json
import os
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

def update_screenshot_status(promote_pending=True):
    """
    Update last_checked for apps that now have screenshots.
    Also promotes Pending apps to Active when they become complete.
    """
    state = load_state()
    updated_count = 0
    promoted_count = 0
    now = datetime.now().isoformat()
    
    for name, data in state.items():
        app_path = os.path.join(APPS_DIR, name)
        
        has_github = data.get('last_updated') and data.get('last_updated') != 'Never' and data.get('last_updated') != 'Unknown'
        
        has_icon = False
        has_screenshot = False
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            has_icon = any('icon' in f.lower() or 'logo' in f.lower() for f in files if f.endswith('.png'))
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
            has_screenshot = len(screenshots) > 0
        
        # App is complete if it has GitHub data, icon, and screenshot
        if has_github and has_icon and has_screenshot:
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
    print(f"Updated last_checked for {updated_count} apps")
    return updated_count

if __name__ == "__main__":
    import sys
    
    promote = not ('--no-promote' in sys.argv)
    update_screenshot_status(promote_pending=promote)


