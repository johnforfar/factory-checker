import os
import subprocess
import json
import requests
import time
import sys

# Configuration
GITHUB_ORG = "miniapp-factory"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "apps")
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")

def run_command(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Don't print error for submodule add failure as it's expected for non-existent repos
        if "git submodule add" not in " ".join(cmd):
            print(f"Error running command {' '.join(cmd)}: {e.stderr}")
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

def get_all_github_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/{GITHUB_ORG}/repos?per_page=100&page={page}"
        print(f"Fetching page {page} of repos...")
        try:
            resp = requests.get(url)
            if resp.status_code != 200:
                print(f"Failed to fetch repos: {resp.status_code} {resp.text}")
                break
            
            data = resp.json()
            if not data:
                break
            
            for repo in data:
                repos.append({
                    "name": repo['name'],
                    "clone_url": repo['clone_url'],
                    "updated_at": repo['updated_at']
                })
            
            page += 1
            if len(data) < 100:
                break
        except Exception as e:
            print(f"Error fetching repos: {e}")
            break
            
    return repos

def update_submodules():
    if not os.path.exists(APPS_DIR):
        os.makedirs(APPS_DIR)
    
    state = load_state()
    repos = get_all_github_repos()
    print(f"Found {len(repos)} repositories.")
    
    updated_apps = []
    repo_root = BASE_DIR

    for repo in repos:
        app_name = repo['name']
        
        # Skip non-app repos if any known ones (like 'xos' is an app)
        # We assume all repos here are apps
        
        # Ensure app is in state file, even if submodule doesn't exist yet
        if app_name not in state:
            state[app_name] = {
                "status": "Pending",
                "last_updated": None,
                "last_checked": None
            }
        
        submodule_path = f"apps/{app_name}"
        full_app_path = os.path.join(repo_root, submodule_path)
        
        # 1. Add/Init Submodule
        if not os.path.exists(full_app_path):
            print(f"Adding submodule for {app_name}...")
            res = run_command(["git", "submodule", "add", "--force", repo['clone_url'], submodule_path], cwd=repo_root)
            if res is None:
                # Still add to state even if submodule add fails
                print(f"Note: {app_name} submodule add failed, but adding to state")
                continue
        
        # 2. Update Submodule
        # print(f"Updating {app_name}...")
        # We only update if we suspect change or first time to save time
        # Actually git submodule update --remote checks for us
        if os.path.exists(full_app_path):
            run_command(["git", "submodule", "update", "--init", "--remote", submodule_path], cwd=repo_root)
            
            # 3. Get Current Commit Hash
            current_hash = run_command(["git", "rev-parse", "HEAD"], cwd=full_app_path)
            
            if current_hash:
                # 4. Compare with State
                last_hash = state.get(app_name, {}).get('last_assessed_hash')
                
                if current_hash != last_hash:
                    print(f"Change detected for {app_name}: {last_hash} -> {current_hash}")
                    updated_apps.append(app_name)
                    
                    # Update state immediately to track "last seen", but "last_assessed" implies visual assessment
                    # We update the hash here to say "we saw this version". 
                    # We need a flag "needs_assessment": True
                    
                    current_data = state.get(app_name, {})
                    current_data['last_seen_hash'] = current_hash
                    current_data['last_updated_ts'] = time.time()
                    current_data['needs_assessment'] = True
                    state[app_name] = current_data

    save_state(state)
    return updated_apps

if __name__ == "__main__":
    updates = update_submodules()
    if updates:
        print(f"\n{len(updates)} apps require assessment: {updates}")
    else:
        print("\nNo apps changed.")



