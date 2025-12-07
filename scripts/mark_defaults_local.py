#!/usr/bin/env python3
"""
Mark apps as Default based on analyzing the local submodule's page.tsx content.
Requires repos to be cloned as submodules in 'apps/'.
"""
import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "apps")

# Default content indicators
DEFAULT_INDICATORS = [
    "Mini App Factory App",
    "This app was created by the Mini App Factory"
]

def check_local_page_content(app_name):
    """Check local page.tsx content for default indicators"""
    page_path = os.path.join(APPS_DIR, app_name, "mini-app", "app", "page.tsx")
    
    if not os.path.exists(page_path):
        return None  # Submodule or file not found
    
    try:
        with open(page_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for indicator in DEFAULT_INDICATORS:
            if indicator in content:
                return True
        return False
        
    except Exception as e:
        print(f"Error reading {page_path}: {e}")
        return None

def mark_defaults_local():
    print("Loading state...")
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    marked_count = 0
    checked_count = 0
    
    print(f"Checking local submodules in {APPS_DIR}...")
    
    if not os.path.exists(APPS_DIR):
        print(f"Apps directory not found: {APPS_DIR}")
        return

    # Filter for apps that have local submodules
    apps_with_submodules = [
        d for d in os.listdir(APPS_DIR) 
        if os.path.isdir(os.path.join(APPS_DIR, d)) and d in state
    ]
    
    print(f"Found {len(apps_with_submodules)} local app submodules.")
    
    for app_name in apps_with_submodules:
        data = state[app_name]
        
        # Skip if already Default
        if data.get('status') == 'Default':
            continue
            
        is_default = check_local_page_content(app_name)
        checked_count += 1
        
        if is_default:
            current_status = data.get('status', 'Unknown')
            print(f"Marking {app_name} as Default (was {current_status}). Reason: Local page.tsx content")
            data['status'] = 'Default'
            data['last_checked'] = datetime.now().isoformat()
            marked_count += 1
    
    if marked_count > 0:
        print(f"\nSaving state with {marked_count} status updates...")
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        print("Done.")
    else:
        print(f"Checked {checked_count} apps. No new defaults found.")

if __name__ == "__main__":
    mark_defaults_local()

