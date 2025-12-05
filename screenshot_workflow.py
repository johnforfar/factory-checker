#!/usr/bin/env python3
"""
Screenshot workflow script - helps process screenshots in batches.
This script:
1. Identifies apps needing screenshots
2. Provides URLs for batch processing
3. Updates last_checked after screenshots are saved
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

def get_apps_needing_screenshots(batch_size=20, include_pending=True):
    """
    Get batch of apps needing screenshots.
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
            needs_screenshots.append((name, status))
            if len(needs_screenshots) >= batch_size:
                break
    
    return needs_screenshots

def generate_urls_batch(batch_size=20, include_pending=True):
    """Generate URLs for a batch of apps"""
    apps = get_apps_needing_screenshots(batch_size, include_pending=include_pending)
    
    print(f"\n{'='*70}")
    print(f"BATCH: {len(apps)} apps needing screenshots")
    if include_pending:
        print(f"(Including Pending, Active, and Default apps)")
    else:
        print(f"(Active and Default apps only)")
    print(f"{'='*70}\n")
    
    for i, (app, status) in enumerate(apps, 1):
        url = f"https://{app}.miniapp-factory.marketplace.openxai.network"
        print(f"{i:2d}. [{status:8s}] {app:30s} -> {url}")
    
    print(f"\n{'='*70}")
    print("INSTRUCTIONS:")
    print("1. Navigate to each URL using browser_navigate")
    print("2. Wait 3 seconds for page to load")
    print("3. Take screenshot using browser_take_screenshot")
    print("4. Save screenshot to: app-review/public/apps/{app}/screenshot-1.png")
    print("5. Run: python3 process_screenshots.py update")
    print(f"{'='*70}\n")
    
    return apps

def update_last_checked_for_complete(promote_pending=True):
    """
    Update last_checked for apps that are now complete.
    Also promotes Pending apps to Active when they become complete.
    """
    state = load_state()
    updated = 0
    promoted = 0
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
                promoted += 1
            
            # Update last_checked if not set or if it's Never
            if not data.get('last_checked') or data.get('last_checked') == 'Never':
                data['last_checked'] = now
                updated += 1
    
    save_state(state)
    if promoted > 0:
        print(f"Promoted {promoted} Pending apps to Active")
    return updated

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'update':
        promote = not (len(sys.argv) > 2 and sys.argv[2] == '--no-promote')
        updated = update_last_checked_for_complete(promote_pending=promote)
        print(f"Updated last_checked for {updated} apps")
    else:
        batch_size = 20
        include_pending = True
        for arg in sys.argv[1:]:
            if arg.isdigit():
                batch_size = int(arg)
            elif arg == '--no-pending':
                include_pending = False
        generate_urls_batch(batch_size, include_pending=include_pending)


