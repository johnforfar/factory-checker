import json
import os

STATE_FILE = "app-review/apps-state.json"
APPS_DIR = "app-review/public/apps"

def main():
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
        
    missing = []
    
    for name, data in state.items():
        # Check if screenshot-1.png exists
        screenshot_path = os.path.join(APPS_DIR, name, "screenshot-1.png")
        if not os.path.exists(screenshot_path):
            missing.append(name)
            
    print(json.dumps(missing))
    # print(f"Found {len(missing)} apps missing screenshot-1.png")

if __name__ == "__main__":
    main()

