#!/usr/bin/env python3
"""
Restore deleted apps from backup and mark them as Inactive
"""
import json
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
BACKUP_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json.bak")
CSV_FILE = os.path.join(BASE_DIR, "app-review", "apps.csv")

def main():
    # Load backup state
    if not os.path.exists(BACKUP_FILE):
        print(f"Backup file not found: {BACKUP_FILE}")
        return
    
    with open(BACKUP_FILE, 'r') as f:
        backup_state = json.load(f)
    
    # Load current state
    with open(STATE_FILE, 'r') as f:
        current_state = json.load(f)
    
    # Load CSV (what exists in GitHub)
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        csv_apps = {row['name'] for row in reader}
    
    # Find apps that were in backup but not in current (deleted apps)
    backup_apps = set(backup_state.keys())
    current_apps = set(current_state.keys())
    deleted_apps = backup_apps - current_apps
    
    if not deleted_apps:
        print("No deleted apps to restore.")
        return
    
    # Restore deleted apps and mark as Inactive
    restored_count = 0
    print(f"Restoring {len(deleted_apps)} deleted apps and marking as Inactive:")
    
    for app_name in sorted(deleted_apps):
        if app_name not in csv_apps:  # Only restore if not in GitHub
            # Restore from backup
            current_state[app_name] = backup_state[app_name].copy()
            # Mark as Inactive
            current_state[app_name]['status'] = 'Inactive'
            restored_count += 1
            print(f"  - {app_name}")
    
    # Save updated state
    with open(STATE_FILE, 'w') as f:
        json.dump(current_state, f, indent=2)
    
    print(f"\n✓ Restored {restored_count} apps and marked as Inactive")
    print(f"State file now has {len(current_state)} apps")

if __name__ == "__main__":
    main()










