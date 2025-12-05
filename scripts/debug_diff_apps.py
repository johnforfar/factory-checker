import json
import csv
import os

BASE_DIR = os.getcwd()
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")

def main():
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    except FileNotFoundError:
        print("State file not found")
        return

    total_apps = len(state)
    checked_apps = 0
    unchecked_apps = []

    for app_name, data in state.items():
        # Definition of "checked" might vary. Let's try to infer.
        last_checked = data.get('last_checked')
        status = data.get('status')
        
        is_checked = False
        if last_checked and last_checked != "Never":
            is_checked = True
        
        if is_checked:
            checked_apps += 1
        else:
            unchecked_apps.append(app_name)

    print(f"Total State apps: {total_apps}")
    print(f"Checked apps (has last_checked): {checked_apps}")
    print(f"Unchecked apps: {len(unchecked_apps)}")
    if unchecked_apps:
        print(f"Unchecked apps list: {unchecked_apps}")

if __name__ == "__main__":
    main()
