import json
import os
from datetime import datetime

STATE_FILE = "app-review/apps-state.json"
APPS_DIR = "app-review/public/apps"

def main():
    if not os.path.exists(STATE_FILE):
        print("State file not found")
        return

    with open(STATE_FILE, 'r') as f:
        state = json.load(f)

    updated_count = 0
    now = datetime.utcnow().isoformat() + "Z"

    for name, data in state.items():
        # Check if app has screenshot
        app_path = os.path.join(APPS_DIR, name)
        has_screenshot = False
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
            has_screenshot = len(screenshots) > 0

        # If it has a screenshot but no last_updated (or invalid), set it
        if has_screenshot:
            last_updated = data.get('last_updated')
            if not last_updated or last_updated == 'Never' or last_updated == 'Unknown':
                print(f"Patching last_updated for {name}")
                state[name]['last_updated'] = now
                updated_count += 1
            
            # Also ensure status is not Pending if it has everything
            if data.get('status') == 'Pending':
                 # We can promote to Active if we are patching the date
                 state[name]['status'] = 'Active'
                 state[name]['last_checked'] = now
                 print(f"  Promoted {name} to Active")
                 updated_count += 1

    if updated_count > 0:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"Updated {updated_count} apps with patched dates.")
    else:
        print("No apps needed patching.")

if __name__ == "__main__":
    main()

