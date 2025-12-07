import os
import hashlib
import json
from collections import Counter

APPS_DIR = "factory-checker/apps"
TEMPLATE_FILE = "ARCHIVE/template/mini-app/app/page.tsx"
STATE_FILE = "factory-checker/app-review/apps-state.json"

def get_file_hash(filepath):
    """Calculate SHA256 hash of a file's content."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def get_file_content(filepath):
    """Read file content."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def main():
    # 1. Get Template Hash
    template_hash = get_file_hash(TEMPLATE_FILE)
    print(f"Template Hash: {template_hash}")
    
    # 2. Check all apps
    if not os.path.exists(APPS_DIR):
        print(f"Apps directory not found: {APPS_DIR}")
        return

    app_dirs = [d for d in os.listdir(APPS_DIR) if os.path.isdir(os.path.join(APPS_DIR, d))]
    print(f"Scanning {len(app_dirs)} apps...")

    hash_map = {} # hash -> list of apps
    defaults = []
    
    for app_name in app_dirs:
        page_path = os.path.join(APPS_DIR, app_name, "mini-app", "app", "page.tsx")
        
        current_hash = get_file_hash(page_path)
        
        if current_hash:
            if current_hash not in hash_map:
                hash_map[current_hash] = []
            hash_map[current_hash].append(app_name)

            if current_hash == template_hash:
                defaults.append(app_name)
        
        elif os.path.exists(page_path):
             # content = get_file_content(page_path)
             # if content and "NEVER write anything here" in content:
             #     defaults.append(app_name)
             pass
                 
    # 3. Analyze Results
    print(f"\nFound {len(defaults)} apps matching the default template.")
    
    print("\nMost common page hashes:")
    sorted_hashes = sorted(hash_map.items(), key=lambda item: len(item[1]), reverse=True)
    
    for h, apps in sorted_hashes[:5]:
        print(f"{h}: {len(apps)} occurrences (e.g., {apps[0]})")

    # 4. Update State File
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        updated_count = 0
        for app in defaults:
            if app in state:
                # Update status to 'Default' if it's currently 'Pending' or similar
                # Or add a specific flag
                if state[app].get('status') != 'Default':
                    state[app]['status'] = 'Default'
                    updated_count += 1
        
        # Save state
        if updated_count > 0:
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"\nUpdated {updated_count} apps to 'Default' status in state file.")
        else:
            print("\nNo state updates needed.")

if __name__ == "__main__":
    main()
