#!/usr/bin/env python3
"""
Batch screenshot processor - processes screenshots in batches efficiently.
This script helps coordinate taking screenshots for multiple apps.
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

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_apps_needing_screenshots(limit=None, include_pending=True):
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
            if limit and len(needs_screenshots) >= limit:
                break
    
    return needs_screenshots

def save_screenshot_from_temp(app_name, temp_path):
    """Save screenshot from temp location to app directory and generate thumbnail"""
    app_dir = os.path.join(APPS_DIR, app_name)
    os.makedirs(app_dir, exist_ok=True)
    
    dest_path = os.path.join(app_dir, "screenshot-1.png")
    if os.path.exists(temp_path):
        subprocess.run(["cp", temp_path, dest_path], check=False)
        if os.path.exists(dest_path):
            # Automatically generate thumbnail
            generate_thumbnail_for_screenshot(dest_path)
            return True
    return False

def generate_thumbnail_for_screenshot(screenshot_path):
    """Generate thumbnail for a screenshot file"""
    try:
        from PIL import Image
        
        if not os.path.exists(screenshot_path):
            return False
        
        # Skip if file is empty
        if os.path.getsize(screenshot_path) == 0:
            return False
        
        # Create thumbnail path
        dir_path = os.path.dirname(screenshot_path)
        filename = os.path.basename(screenshot_path)
        name, ext = os.path.splitext(filename)
        thumbnail_path = os.path.join(dir_path, f"{name}-thumb{ext}")
        
        # Skip if thumbnail already exists and is newer
        if os.path.exists(thumbnail_path):
            if os.path.getmtime(thumbnail_path) >= os.path.getmtime(screenshot_path):
                return True
        
        # Create thumbnail
        with Image.open(screenshot_path) as img:
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            
            # Create thumbnail maintaining aspect ratio (300x200 max)
            img.thumbnail((300, 200), Image.Resampling.LANCZOS)
            
            # Save optimized thumbnail
            img.save(thumbnail_path, 'PNG', optimize=True, compress_level=9)
            return True
    except Exception as e:
        # Silently fail - thumbnail generation is optional
        return False

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
        # Parse arguments
        limit = None
        include_pending = True
        for arg in sys.argv[1:]:
            if arg.isdigit():
                limit = int(arg)
            elif arg == '--no-pending':
                include_pending = False
        
        apps = get_apps_needing_screenshots(limit=limit, include_pending=include_pending)
        total = len(apps)
        
        print(f"\n{'='*70}")
        print(f"BATCH SCREENSHOT PROCESSOR")
        print(f"Apps needing screenshots: {total}")
        if include_pending:
            print(f"(Including Pending, Active, and Default apps)")
        else:
            print(f"(Active and Default apps only)")
        print(f"{'='*70}\n")
        
        if total == 0:
            print("✅ All apps already have screenshots!")
            updated = update_last_checked_for_complete()
            if updated > 0:
                print(f"Updated last_checked for {updated} apps")
            exit(0)
        
        print(f"Processing {total} apps:\n")
        for i, (name, url, status) in enumerate(apps, 1):
            print(f"{i:3d}. [{status:8s}] {name:35s} -> {url}")

