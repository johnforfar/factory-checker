import json
import os

BASE_DIR = os.getcwd()
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")

APPS_TO_UPDATE = ['calfit-checker', 'hilderose', 'lodebina', 'mdot', 'omni-base', 'orb-runner', 'slots']

def main():
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
    except FileNotFoundError:
        print("State file not found")
        return

    count = 0
    for app_name in APPS_TO_UPDATE:
        if app_name in state:
            state[app_name]['needs_full_update'] = True
            count += 1
            print(f"Marked {app_name} for full update")
        else:
            print(f"App {app_name} not found in state")

    if count > 0:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        print(f"Updated {count} apps in state file")

if __name__ == "__main__":
    main()

