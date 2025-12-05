#!/usr/bin/env python3
"""
Mark apps as 'Inactive' if they no longer exist in GitHub/CSV
"""
import json
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
CSV_FILE = os.path.join(BASE_DIR, "app-review", "apps.csv")

def main():
    # Load state
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    # Load CSV (source of truth for what exists in GitHub)
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        csv_apps = {row['name'] for row in reader}
    
    # Find apps in state that don't exist in CSV/GitHub
    state_apps = set(state.keys())
    missing_from_github = state_apps - csv_apps
    
    if not missing_from_github:
        print("No apps to mark as inactive. State file is in sync with GitHub.")
        return
    
    marked_count = 0
    already_inactive = 0
    
    print(f"Marking {len(missing_from_github)} apps as 'Inactive' (no longer exist in GitHub):")
    for app in sorted(missing_from_github):
        if state[app].get('status') == 'Inactive':
            already_inactive += 1
            print(f"  - {app} (already Inactive)")
        else:
            state[app]['status'] = 'Inactive'
            marked_count += 1
            print(f"  - {app}")
    
    # Save updated state
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"\n✓ Marked {marked_count} apps as Inactive")
    if already_inactive > 0:
        print(f"  ({already_inactive} were already marked as Inactive)")
    print(f"State file has {len(state)} apps total ({len(csv_apps)} active in GitHub, {len(missing_from_github)} inactive)")

if __name__ == "__main__":
    main()

