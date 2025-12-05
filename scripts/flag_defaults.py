import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "apps")

def check_is_default(app_name):
    metadata_path = os.path.join(APPS_DIR, app_name, "mini-app", "lib", "metadata.ts")
    
    if not os.path.exists(metadata_path):
        return False
        
    try:
        with open(metadata_path, 'r') as f:
            content = f.read()
            if 'title = "Mini App Factory App"' in content:
                return True
            if 'description = "This app was created by the Mini App Factory!"' in content:
                return True
    except Exception as e:
        print(f"Error reading {app_name}: {e}")
        
    return False

def main():
    if not os.path.exists(STATE_FILE):
        print("State file not found.")
        return

    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    count = 0
    for app in state:
        is_default = check_is_default(app)
        
        # Reset status if not default (unless it was manually set to Default? No, automate it)
        if is_default:
            state[app]['status'] = "Default"
            state[app]['title'] = "Mini App Factory App"
            count += 1
        else:
            # If we don't have a title, try to extract it?
            # For now, set status to Active if it was Default
            if state[app].get('status') == "Default":
                state[app]['status'] = "Active"
            if state[app].get('status') == "Pending":
                state[app]['status'] = "Active"

    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
        
    print(f"Flagged {count} default apps based on metadata.")

if __name__ == "__main__":
    main()
