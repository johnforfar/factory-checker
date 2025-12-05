#!/usr/bin/env python3
"""
Check all apps to determine their status and update last_checked.
This marks apps as 'checked' once we've determined their status (Active, Default, Inactive, etc.)
"""
import json
import os
import subprocess
import time
import random
import concurrent.futures
from bs4 import BeautifulSoup
from datetime import datetime
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
CSV_FILE = os.path.join(BASE_DIR, "app-review", "apps.csv")
APPS_DIR = os.path.join(BASE_DIR, "apps")
APPS_PUBLIC_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def check_app_status(app_name):
    """Check if app exists in GitHub and determine status"""
    time.sleep(random.uniform(0.5, 1.5))
    
    # Check if app exists in GitHub
    url = f"https://github.com/miniapp-factory/{app_name}"
    ua = random.choice(USER_AGENTS)
    
    try:
        cmd = ["curl", "-s", "-H", f"User-Agent: {ua}", "--max-time", "5", url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
        
        if result.returncode != 0 or "Not Found" in result.stdout or "404" in result.stdout:
            return app_name, "Inactive", "Not found in GitHub"
        
        # Check metadata.ts for default status
        metadata_url = f"https://raw.githubusercontent.com/miniapp-factory/{app_name}/main/mini-app/lib/metadata.ts"
        cmd = ["curl", "-s", "-H", f"User-Agent: {ua}", "--max-time", "5", metadata_url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
        
        if result.returncode == 0 and result.stdout:
            content = result.stdout
            # Check for default title
            if 'title = "Mini App Factory App"' in content or 'title: "Mini App Factory App"' in content:
                return app_name, "Default", "Found default template"
            else:
                return app_name, "Active", "Found custom app"
        
        return app_name, "Active", "Exists in GitHub"
        
    except Exception as e:
        return app_name, None, f"Error: {e}"

def main():
    state = load_state()
    
    # Load CSV to know which apps exist in GitHub
    csv_apps = set()
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            csv_apps = {row['name'] for row in reader}
    
    # Get all apps that need checking
    apps_to_check = []
    apps_needing_inactive = []
    apps_needing_status = []
    apps_needing_checked = []
    
    for app_name, app_data in state.items():
        current_status = app_data.get('status', 'Pending')
        last_checked = app_data.get('last_checked', 'Never')
        exists_in_github = app_name in csv_apps
        
        # First priority: Mark as Inactive if not in GitHub
        if not exists_in_github and current_status != 'Inactive':
            apps_needing_inactive.append(app_name)
            apps_to_check.append((app_name, 'check_inactive'))
        # Second priority: Check status for Pending apps in GitHub
        elif exists_in_github and current_status == 'Pending':
            apps_needing_status.append(app_name)
            apps_to_check.append((app_name, 'check_status'))
        # Third priority: Mark as checked if they have a status but no last_checked
        elif (last_checked == 'Never' or not last_checked) and current_status != 'Pending':
            apps_needing_checked.append(app_name)
            apps_to_check.append((app_name, 'mark_checked'))
    
    print(f"Total apps in state: {len(state)}")
    print(f"Apps needing checks: {len(apps_to_check)}")
    print(f"\nBreakdown:")
    print(f"  - Need inactive check: {len(apps_needing_inactive)}")
    print(f"  - Need status check: {len(apps_needing_status)}")
    print(f"  - Need last_checked update: {len(apps_needing_checked)}")
    
    now = datetime.now().isoformat()
    updated_count = 0
    inactive_count = 0
    status_updated_count = 0
    checked_count = 0
    
    # First, mark apps as Inactive if they don't exist in GitHub
    for app_name, check_type in apps_to_check:
        if check_type == 'check_inactive':
            if app_name not in csv_apps:
                state[app_name]['status'] = 'Inactive'
                state[app_name]['last_checked'] = now
                inactive_count += 1
                updated_count += 1
    
    # Then check status for Pending apps that exist in GitHub
    apps_needing_status_check = [app_name for app_name, check_type in apps_to_check if check_type == 'check_status']
    
    if apps_needing_status_check:
        print(f"\nChecking status for {len(apps_needing_status_check)} apps...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_app = {executor.submit(check_app_status, app): app for app in apps_needing_status_check}
            
            processed = 0
            for future in concurrent.futures.as_completed(future_to_app):
                app_name = future_to_app[future]
                processed += 1
                try:
                    name, status, reason = future.result()
                    if status:
                        old_status = state[name].get('status', 'Pending')
                        state[name]['status'] = status
                        state[name]['last_checked'] = now
                        if old_status != status:
                            status_updated_count += 1
                        checked_count += 1
                        updated_count += 1
                        
                        if processed % 10 == 0:
                            print(f"  Processed {processed}/{len(apps_needing_status_check)}...")
                            save_state(state)  # Save periodically
                except Exception as exc:
                    print(f"  Error checking {app_name}: {exc}")
    
    # Finally, mark remaining apps as checked if they have a status but no last_checked
    for app_name, check_type in apps_to_check:
        if check_type == 'mark_checked':
            if state[app_name].get('status') and state[app_name].get('status') != 'Pending':
                if not state[app_name].get('last_checked') or state[app_name].get('last_checked') == 'Never':
                    state[app_name]['last_checked'] = now
                    checked_count += 1
                    updated_count += 1
    
    # Save final state
    save_state(state)
    
    print(f"\n{'='*70}")
    print(f"CHECK COMPLETE")
    print(f"{'='*70}")
    print(f"Marked as Inactive: {inactive_count}")
    print(f"Status updated: {status_updated_count}")
    print(f"Marked as checked: {checked_count}")
    print(f"Total apps updated: {updated_count}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()

