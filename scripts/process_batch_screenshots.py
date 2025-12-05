#!/usr/bin/env python3
"""
Process screenshots in batches and update last_checked.
This script can be run repeatedly to process remaining apps.
"""
import json
import os
import subprocess
import sys
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

def get_apps_needing_screenshots(include_pending=True, limit=None):
    """Get apps that need screenshots"""
    state = load_state()
    needs_screenshots = []
    
    for name, data in state.items():
        status = data.get('status', 'Pending')
        
        if not include_pending and status == 'Pending':
            continue
        
        app_path = os.path.join(APPS_DIR, name)
        screenshots = []
        
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower() and 'thumb' not in f.lower()]
        
        if len(screenshots) == 0:
            url = data.get('landing_url')
            if not url:
                url = f"https://{name}.miniapp-factory.marketplace.openxai.network"
            needs_screenshots.append((name, url, status))
            if limit and len(needs_screenshots) >= limit:
                break
    
    return needs_screenshots

def update_last_checked_for_complete(promote_pending=True):
    """Update last_checked for apps that are now complete"""
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
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower() and 'thumb' not in f.lower()]
            has_screenshot = len(screenshots) > 0
        
        if has_github and has_icon and has_screenshot:
            if promote_pending and data.get('status') == 'Pending':
                data['status'] = 'Active'
                promoted += 1
            
            if not data.get('last_checked') or data.get('last_checked') == 'Never':
                data['last_checked'] = now
                updated += 1
    
    save_state(state)
    if promoted > 0:
        print(f"Promoted {promoted} Pending apps to Active")
    return updated

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Process screenshots in batches')
    parser.add_argument('--batch-size', type=int, default=20, help='Number of apps per batch')
    parser.add_argument('--update-only', action='store_true', help='Only update last_checked')
    parser.add_argument('--no-pending', action='store_true', help='Exclude Pending apps')
    parser.add_argument('--no-promote', action='store_true', help='Do not promote Pending to Active')
    
    args = parser.parse_args()
    
    if args.update_only:
        updated = update_last_checked_for_complete(promote_pending=not args.no_promote)
        print(f"✅ Updated last_checked for {updated} apps")
        return
    
    apps = get_apps_needing_screenshots(include_pending=not args.no_pending, limit=args.batch_size)
    total = len(get_apps_needing_screenshots(include_pending=not args.no_pending))
    
    print(f"\n{'='*70}")
    print(f"BATCH SCREENSHOT PROCESSOR")
    print(f"Total apps needing screenshots: {total}")
    print(f"Batch size: {len(apps)}")
    print(f"{'='*70}\n")
    
    if len(apps) == 0:
        print("✅ All apps already have screenshots!")
        updated = update_last_checked_for_complete(promote_pending=not args.no_promote)
        if updated > 0:
            print(f"Updated last_checked for {updated} apps")
        return
    
    print("Apps in this batch:\n")
    for i, (name, url, status) in enumerate(apps, 1):
        print(f"{i:3d}. [{status:8s}] {name:35s} -> {url}")
    
    print(f"\n{'='*70}")
    print("After taking screenshots, run:")
    print("  python3 process_batch_screenshots.py --update-only")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()










