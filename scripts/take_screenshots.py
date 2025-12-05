#!/usr/bin/env python3
"""
Script to take screenshots for apps that need them.
This script identifies apps needing screenshots and outputs them in batches.
The agent will use browser tools to take screenshots.
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

def get_apps_needing_screenshots(state, include_pending=True):
    """
    Get list of apps that need screenshots.
    By default includes ALL apps (Pending, Active, Default).
    """
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

def update_last_checked(state, app_name):
    """Update last_checked timestamp for an app"""
    if app_name in state:
        state[app_name]['last_checked'] = datetime.now().isoformat()

def main():
    import sys
    
    include_pending = not ('--no-pending' in sys.argv)
    state = load_state()
    needs_screenshots = get_apps_needing_screenshots(state, include_pending=include_pending)
    
    print(f"\n{'='*70}")
    print(f"SCREENSHOT TAKER - Browser Automation Ready")
    print(f"Total apps needing screenshots: {len(needs_screenshots)}")
    if include_pending:
        print(f"(Including Pending, Active, and Default apps)")
    else:
        print(f"(Active and Default apps only)")
    print(f"{'='*70}\n")
    
    print(f"First 50 apps to process:\n")
    for i, (app, url, status) in enumerate(needs_screenshots[:50], 1):
        print(f"{i:3d}. [{status:8s}] {app:35s} -> {url}")
    
    if len(needs_screenshots) > 50:
        print(f"\n... and {len(needs_screenshots) - 50} more apps")
    
    print(f"\n{'='*70}")
    print("READY FOR BROWSER AUTOMATION")
    print("The agent will use browser tools to take screenshots for these apps.")
    print(f"{'='*70}\n")
    
    return needs_screenshots

if __name__ == "__main__":
    main()


