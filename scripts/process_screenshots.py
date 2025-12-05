#!/usr/bin/env python3
"""
Process screenshots and update last_checked status.
This script:
1. Identifies apps that need screenshots (ALL apps including Pending)
2. After screenshots are taken, updates last_checked to reflect all checks are complete
3. Promotes Pending apps to Active when they become complete
Goal: Move all apps to Completed status (has status, icon, screenshots, last_checked, GitHub data)
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

def is_app_complete(data, app_path):
    """Check if an app has all required data for completion"""
    # Check status (must not be Pending - but we'll update Pending to Active if complete)
    has_status = data.get('status') and data.get('status') != 'Pending'
    
    # Check GitHub update date
    has_github = data.get('last_updated') and data.get('last_updated') != 'Never' and data.get('last_updated') != 'Unknown'
    
    # Check icon
    has_icon = False
    if os.path.exists(app_path):
        files = os.listdir(app_path)
        has_icon = any('icon' in f.lower() or 'logo' in f.lower() for f in files if f.endswith('.png'))
    
    # Check screenshot
    has_screenshot = False
    if os.path.exists(app_path):
        files = os.listdir(app_path)
        screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
        has_screenshot = len(screenshots) > 0
    
    return has_status and has_github and has_icon and has_screenshot

def is_app_complete_including_pending(data, app_path):
    """Check if an app has all required data, even if currently Pending"""
    # Check GitHub update date
    has_github = data.get('last_updated') and data.get('last_updated') != 'Never' and data.get('last_updated') != 'Unknown'
    
    # Check icon
    has_icon = False
    if os.path.exists(app_path):
        files = os.listdir(app_path)
        has_icon = any('icon' in f.lower() or 'logo' in f.lower() for f in files if f.endswith('.png'))
    
    # Check screenshot
    has_screenshot = False
    if os.path.exists(app_path):
        files = os.listdir(app_path)
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
        
        # Check if app is complete (including Pending apps)
        is_complete = is_app_complete_including_pending(data, app_path)
        
        if is_complete:
            # Promote Pending to Active if requested
            if promote_pending and data.get('status') == 'Pending':
                data['status'] = 'Active'
                promoted_count += 1
            
            # Update last_checked if not set or if it's Never
            if not data.get('last_checked') or data.get('last_checked') == 'Never':
                data['last_checked'] = now
                updated_count += 1
    
    save_state(state)
    print(f"Updated last_checked for {updated_count} apps")
    if promoted_count > 0:
        print(f"Promoted {promoted_count} Pending apps to Active")
    return updated_count, promoted_count

def get_apps_needing_screenshots(include_pending=True):
    """
    Get list of apps that need screenshots.
    By default includes ALL apps (Pending, Active, Default).
    """
    state = load_state()
    needs_screenshots = []
    
    for name, data in state.items():
        # Skip if we're not including Pending and app is Pending
        if not include_pending and data.get('status') == 'Pending':
            continue
        
        app_path = os.path.join(APPS_DIR, name)
        screenshots = []
        
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
        
        if len(screenshots) == 0:
            status = data.get('status', 'Pending')
            url = f"https://{name}.miniapp-factory.marketplace.openxai.network"
            needs_screenshots.append((name, url, status))
    
    return needs_screenshots

def get_completion_stats():
    """Get statistics on app completion"""
    state = load_state()
    total = len(state)
    complete = 0
    incomplete = 0
    
    for name, data in state.items():
        app_path = os.path.join(APPS_DIR, name)
        if is_app_complete(data, app_path):
            complete += 1
        else:
            incomplete += 1
    
    return {
        'total': total,
        'complete': complete,
        'incomplete': incomplete
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'update':
        # Update last_checked for complete apps and promote Pending
        promote = not (len(sys.argv) > 2 and sys.argv[2] == '--no-promote')
        update_last_checked_for_complete_apps(promote_pending=promote)
    elif len(sys.argv) > 1 and sys.argv[1] == 'stats':
        # Show completion statistics
        stats = get_completion_stats()
        print(f"Total apps: {stats['total']}")
        print(f"Complete: {stats['complete']}")
        print(f"Incomplete: {stats['incomplete']}")
        
        # Show breakdown by status
        state = load_state()
        status_counts = {'Pending': 0, 'Active': 0, 'Default': 0}
        for name, data in state.items():
            status = data.get('status', 'Pending')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"\nBy status:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
    else:
        # Show apps needing screenshots (all apps by default)
        include_pending = len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] != '--no-pending')
        needs = get_apps_needing_screenshots(include_pending=include_pending)
        
        print(f"\n{'='*70}")
        print(f"APPS NEEDING SCREENSHOTS")
        print(f"Total: {len(needs)}")
        if include_pending:
            print(f"(Including Pending, Active, and Default apps)")
        else:
            print(f"(Active and Default apps only)")
        print(f"{'='*70}\n")
        
        if len(needs) == 0:
            print("✅ All apps already have screenshots!")
        else:
            print(f"First 50 apps:\n")
            for i, (name, url, status) in enumerate(needs[:50], 1):
                print(f"{i:3d}. [{status:8s}] {name:35s} -> {url}")
            if len(needs) > 50:
                print(f"\n... and {len(needs) - 50} more apps")
            print(f"\nRun 'python3 process_screenshots.py update' after taking screenshots")


