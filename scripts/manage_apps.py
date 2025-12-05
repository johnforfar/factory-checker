import os
import subprocess
import json
import csv

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "apps")
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
CSV_FILE = os.path.join(BASE_DIR, "app-review", "apps.csv")

def run_command(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Suppress error for expected submodule add failures
        pass
        return None

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_apps_from_csv():
    apps = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                apps.append(row)
    return apps

def update_submodules():
    if not os.path.exists(APPS_DIR):
        os.makedirs(APPS_DIR)
    
    state = load_state()
    apps = get_apps_from_csv()
    print(f"Processing {len(apps)} apps...")
    
    updated_apps = []
    repo_root = BASE_DIR

    for app in apps:
        app_name = app['name']
        submodule_path = f"apps/{app_name}"
        full_app_path = os.path.join(repo_root, submodule_path)
        
        # 1. Add Submodule (if missing)
        if not os.path.exists(full_app_path):
            print(f"Adding {app_name}...")
            run_command(["git", "submodule", "add", "--force", app['repo_url'], submodule_path], cwd=repo_root)
        
        # 2. Check Hash
        current_hash = run_command(["git", "rev-parse", "HEAD"], cwd=full_app_path)
        
        if not current_hash:
            continue

        last_hash = state.get(app_name, {}).get('last_assessed_hash')
        
        if current_hash != last_hash:
            print(f"Change: {app_name} ({last_hash or 'New'} -> {current_hash})")
            
            # Check if Default
            # Heuristic: If we can read package.json or similar? 
            # Or we just rely on visual assessment later.
            
            state[app_name] = {
                "last_assessed_hash": current_hash,
                "last_updated": os.path.getmtime(full_app_path),
                "title": state.get(app_name, {}).get('title', app['title']),
                "status": state.get(app_name, {}).get('status', 'Pending')
            }
            updated_apps.append(app_name)

    save_state(state)
    
    # Batch Update at end for efficiency
    print("Syncing submodules...")
    run_command(["git", "submodule", "update", "--init", "--recursive", "--jobs", "8"], cwd=repo_root)
    
    return updated_apps

if __name__ == "__main__":
    updates = update_submodules()
    print(f"\n{len(updates)} apps need assessment.")
