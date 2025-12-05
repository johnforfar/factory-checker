#!/usr/bin/env python3
"""
Fast screenshot processor - processes multiple apps efficiently
"""
import json
import os
import subprocess
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")
TEMP_DIR = "/var/folders/bn/ml8l4wps6770plhr2r14g0dm0000gn/T/cursor/screenshots"

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_apps_needing_screenshots(limit=None):
    """Get apps that need screenshots"""
    state = load_state()
    needs_screenshots = []
    
    for name, data in state.items():
        app_path = os.path.join(APPS_DIR, name)
        screenshots = []
        
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
        
        if len(screenshots) == 0:
            url = f"https://{name}.miniapp-factory.marketplace.openxai.network"
            status = data.get('status', 'Pending')
            needs_screenshots.append((name, url, status))
            if limit and len(needs_screenshots) >= limit:
                break
    
    return needs_screenshots

def save_screenshot_from_temp(app_name, temp_filename):
    """Save screenshot from temp to app directory"""
    app_dir = os.path.join(APPS_DIR, app_name)
    temp_path = os.path.join(TEMP_DIR, temp_filename)
    dest_path = os.path.join(app_dir, "screenshot-1.png")
    
    if not os.path.exists(temp_path):
        return False
    
    os.makedirs(app_dir, exist_ok=True)
    try:
        subprocess.run(["cp", temp_path, dest_path], check=True, capture_output=True)
        return True
    except:
        return False

def update_last_checked_for_complete():
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
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
            has_screenshot = len(screenshots) > 0
        
        if has_github and has_icon and has_screenshot:
            if data.get('status') == 'Pending':
                data['status'] = 'Active'
                promoted += 1
            
            if not data.get('last_checked') or data.get('last_checked') == 'Never':
                data['last_checked'] = now
                updated += 1
    
    save_state(state)
    return updated, promoted

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Fast screenshot processor')
    parser.add_argument('--batch-size', type=int, default=30, help='Batch size')
    parser.add_argument('--update-only', action='store_true', help='Only update last_checked')
    parser.add_argument('--save-from-temp', action='store_true', help='Save screenshots from temp directory')
    
    args = parser.parse_args()
    
    if args.update_only:
        updated, promoted = update_last_checked_for_complete()
        print(f"✅ Updated last_checked for {updated} apps")
        if promoted > 0:
            print(f"Promoted {promoted} Pending apps to Active")
        sys.exit(0)
    
    if args.save_from_temp:
        # Get list of temp screenshots
        if os.path.exists(TEMP_DIR):
            temp_files = [f for f in os.listdir(TEMP_DIR) if f.endswith('.png') and 'screenshot' in f]
            saved = 0
            for temp_file in temp_files:
                # Extract app name from filename (e.g., "app-name-screenshot.png" -> "app-name")
                app_name = temp_file.replace('-screenshot.png', '').replace('_screenshot.png', '')
                if save_screenshot_from_temp(app_name, temp_file):
                    saved += 1
            print(f"Saved {saved} screenshots from temp directory")
        sys.exit(0)
    
    apps = get_apps_needing_screenshots(limit=args.batch_size)
    total = len(get_apps_needing_screenshots())
    
    print(f"\n{'='*70}")
    print(f"FAST SCREENSHOT PROCESSOR")
    print(f"Total apps needing screenshots: {total}")
    print(f"Batch size: {len(apps)}")
    print(f"{'='*70}\n")
    
    if len(apps) == 0:
        print("✅ All apps already have screenshots!")
        updated, promoted = update_last_checked_for_complete()
        if updated > 0:
            print(f"Updated last_checked for {updated} apps")
        sys.exit(0)
    
    print("Apps in this batch:\n")
    for i, (name, url, status) in enumerate(apps, 1):
        print(f"{i:3d}. [{status:8s}] {name:35s} -> {url}")
    
    print(f"\n{'='*70}")
    print("After taking screenshots:")
    print("  python3 fast_screenshot_processor.py --save-from-temp")
    print("  python3 fast_screenshot_processor.py --update-only")
    print(f"{'='*70}\n")












