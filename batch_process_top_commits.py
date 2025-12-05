#!/usr/bin/env python3
"""
Batch process screenshots for top 500 apps by commits.
This script uses browser automation to take screenshots.
"""
import json
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def get_top_commits_apps_needing_screenshots(limit=500, include_pending=True):
    """Get top apps by commits that need screenshots"""
    state = load_state()
    apps_with_commits = []
    
    for name, data in state.items():
        status = data.get('status', 'Pending')
        if not include_pending and status == 'Pending':
            continue
        
        app_path = os.path.join(APPS_DIR, name)
        screenshots = []
        
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
        
        if len(screenshots) == 0:
            commits = data.get('commits', 0) or 0
            url = f"https://{name}.miniapp-factory.marketplace.openxai.network"
            apps_with_commits.append((name, url, status, commits))
    
    apps_with_commits.sort(key=lambda x: (-x[3], x[0]))
    return apps_with_commits[:limit]

def save_screenshot(app_name, temp_path):
    """Save screenshot from temp location to app directory"""
    app_dir = os.path.join(APPS_DIR, app_name)
    os.makedirs(app_dir, exist_ok=True)
    
    dest_path = os.path.join(app_dir, "screenshot-1.png")
    
    # Copy file
    import shutil
    shutil.copy2(temp_path, dest_path)
    
    print(f"  ✓ Saved screenshot for {app_name}")
    return dest_path

if __name__ == "__main__":
    apps = get_top_commits_apps_needing_screenshots(limit=500, include_pending=True)
    
    print(f"\n{'='*70}")
    print(f"BATCH PROCESSING TOP {len(apps)} APPS BY COMMITS")
    print(f"{'='*70}\n")
    
    if len(apps) == 0:
        print("✅ All apps already have screenshots!")
        sys.exit(0)
    
    print(f"Apps to process: {len(apps)}")
    print(f"\nNote: This script outputs the list of apps.")
    print(f"Use browser automation tools to take screenshots for each app.")
    print(f"\nFirst 50 apps:\n")
    
    for i, (name, url, status, commits) in enumerate(apps[:50], 1):
        print(f"{i:3d}. [{status:8s}] {name:40s} ({commits:4d} commits) -> {url}")
    
    if len(apps) > 50:
        print(f"\n... and {len(apps) - 50} more apps")
    
    print(f"\n{'='*70}")
    print(f"Full list ({len(apps)} apps):")
    print(f"{'='*70}")
    for i, (name, url, status, commits) in enumerate(apps, 1):
        print(f"{i:4d}. {name}")












