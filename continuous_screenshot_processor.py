#!/usr/bin/env python3
"""
Continuous screenshot processor - processes all remaining apps in batches
until all screenshots are complete.
"""
import json
import os
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

def get_all_apps_needing_screenshots(include_pending=True):
    """
    Get all apps needing screenshots.
    By default includes ALL apps (Pending, Active, Default).
    """
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    needing_screenshots = []
    for name, data in state.items():
        status = data.get('status', 'Pending')
        
        # Skip Pending if not including them
        if not include_pending and status == 'Pending':
            continue
        
        app_path = os.path.join(APPS_DIR, name)
        has_screenshots = False
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
            has_screenshots = len(screenshots) > 0
        
        if not has_screenshots:
            needing_screenshots.append((name, status))
    
    return needing_screenshots

if __name__ == "__main__":
    import sys
    
    include_pending = not ('--no-pending' in sys.argv)
    apps = get_all_apps_needing_screenshots(include_pending=include_pending)
    total = len(apps)
    
    print(f"\n{'='*70}")
    print(f"CONTINUOUS SCREENSHOT PROCESSOR")
    print(f"Total apps needing screenshots: {total}")
    if include_pending:
        print(f"(Including Pending, Active, and Default apps)")
    else:
        print(f"(Active and Default apps only)")
    print(f"{'='*70}\n")
    
    if total == 0:
        print("✅ All apps already have screenshots!")
        exit(0)
    
    # Process in batches of 30
    batch_size = 30
    total_batches = (total + batch_size - 1) // batch_size
    
    print(f"Will process {total} apps in {total_batches} batches of {batch_size}")
    print(f"\nBatch list (for manual processing):\n")
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total)
        batch = apps[start_idx:end_idx]
        
        print(f"\n--- BATCH {batch_num + 1}/{total_batches} ({len(batch)} apps) ---")
        for i, (app, status) in enumerate(batch, 1):
            url = f"https://{app}.miniapp-factory.marketplace.openxai.network"
            print(f"{i:2d}. [{status:8s}] {app:30s} -> {url}")


