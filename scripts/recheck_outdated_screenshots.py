import json
import os
from datetime import datetime, timezone

STATE_FILE = "app-review/apps-state.json"

def parse_date(date_str):
    if not date_str:
        return None
    try:
        # Handle "2025-11-26T12:15:15Z" -> make timezone aware
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None

def main():
    print("Checking for outdated screenshots...")
    
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
        
    outdated_apps = []
    
    for app_name, data in state.items():
        last_updated_str = data.get('last_updated')
        last_checked_str = data.get('last_checked')
        
        updated_date = parse_date(last_updated_str)
        checked_date = parse_date(last_checked_str)
        
        if updated_date and checked_date:
            # If GitHub update is NEWER than last screenshot check
            if updated_date > checked_date:
                print(f"Outdated: {app_name} (Updated: {last_updated_str} > Checked: {last_checked_str})")
                outdated_apps.append(app_name)
        elif updated_date and not checked_date:
             # Has update but never checked
             print(f"New/Unchecked: {app_name}")
             outdated_apps.append(app_name)

    print(f"\nFound {len(outdated_apps)} apps needing screenshot updates due to recent commits.")
    
    if outdated_apps:
        print("Marking them as Pending for screenshot processing...")
        # Mark them as Pending (or just clear last_checked so they get picked up)
        # Actually, let's just delete their screenshots so continue_screenshot_processing.py picks them up naturally
        
        for app in outdated_apps:
            # Update state to force re-check
            state[app]['last_checked'] = None 
            state[app]['status'] = 'Pending' # Optional, but helps visibility
            
            # Remove existing screenshot to force retake
            screenshot_path = f"app-review/public/apps/{app}/screenshot-1.png"
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                print(f"  - Deleted old screenshot for {app}")
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
            
        print("\nReady to process updates. Run 'continue_screenshot_processing.py' next.")
    else:
        print("All screenshots are up to date.")

if __name__ == "__main__":
    main()

