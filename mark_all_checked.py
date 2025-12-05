#!/usr/bin/env python3
"""
Mark all apps as checked if they have a determined status.
This ensures that any app with a status (Active, Default, Inactive, etc.) is marked as checked.
"""
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")

def main():
    
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    now = datetime.now().isoformat()
    updated_count = 0
    
    for app_name, app_data in state.items():
        status = app_data.get('status', 'Pending')
        last_checked = app_data.get('last_checked', 'Never')
        
        # If app has a determined status (not Pending), mark as checked
        if status != 'Pending':
            if not last_checked or last_checked == 'Never':
                app_data['last_checked'] = now
                updated_count += 1
    
    if updated_count > 0:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"✓ Marked {updated_count} apps as checked")
    else:
        print("All apps with determined status are already marked as checked")
    
    # Count by status
    status_counts = {}
    for app_name, app_data in state.items():
        status = app_data.get('status', 'Pending')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print(f"\nApps by status:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

if __name__ == "__main__":
    main()

