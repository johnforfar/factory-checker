#!/usr/bin/env python3
"""
Process screenshots for top 500 apps by commit count.
This script:
1. Gets all apps sorted by commits (descending)
2. Filters to those needing screenshots
3. Processes up to 500 apps
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def get_top_commits_apps_needing_screenshots(limit=500, include_pending=True):
    """
    Get top apps by commits that need screenshots.
    
    Args:
        limit: Maximum number of apps to return
        include_pending: Whether to include Pending apps
    """
    state = load_state()
    
    # Build list of all apps with their commit counts
    apps_with_commits = []
    
    for name, data in state.items():
        status = data.get('status', 'Pending')
        
        # Skip Pending if not including them
        if not include_pending and status == 'Pending':
            continue
        
        # Check if app needs screenshots
        app_path = os.path.join(APPS_DIR, name)
        screenshots = []
        
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
        
        # Only include apps that need screenshots
        if len(screenshots) == 0:
            commits = data.get('commits', 0) or 0
            url = f"https://{name}.miniapp-factory.marketplace.openxai.network"
            apps_with_commits.append((name, url, status, commits))
    
    # Sort by commits (descending), then by name
    apps_with_commits.sort(key=lambda x: (-x[3], x[0]))
    
    # Return top N
    return apps_with_commits[:limit]

if __name__ == "__main__":
    apps = get_top_commits_apps_needing_screenshots(limit=500, include_pending=True)
    
    print(f"\n{'='*70}")
    print(f"TOP 500 APPS BY COMMITS NEEDING SCREENSHOTS")
    print(f"Total: {len(apps)}")
    print(f"{'='*70}\n")
    
    if len(apps) == 0:
        print("✅ All top apps already have screenshots!")
    else:
        print(f"First 50 apps:\n")
        for i, (name, url, status, commits) in enumerate(apps[:50], 1):
            print(f"{i:3d}. [{status:8s}] {name:35s} ({commits:4d} commits) -> {url}")
        if len(apps) > 50:
            print(f"\n... and {len(apps) - 50} more apps")
        
        print(f"\n{'='*70}")
        print(f"Processing {len(apps)} apps...")
        print(f"{'='*70}\n")
        
        # Output all apps for batch processing
        for i, (name, url, status, commits) in enumerate(apps, 1):
            print(f"{i:4d}. [{status:8s}] {name:40s} ({commits:4d} commits)")












