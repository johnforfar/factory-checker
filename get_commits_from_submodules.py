import json
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "apps")

def get_commit_count(app_name):
    """Get commit count from local git repo."""
    repo_path = os.path.join(APPS_DIR, app_name)
    git_dir = os.path.join(repo_path, ".git")
    
    if not os.path.exists(git_dir):
        return None
    
    try:
        # Use git rev-list --count HEAD to get total commits
        result = subprocess.run(
            ["git", "-C", repo_path, "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            count = int(result.stdout.strip())
            return count
        else:
            return None
    except Exception as e:
        print(f"Error getting commits for {app_name}: {e}")
        return None

def main():
    if not os.path.exists(STATE_FILE):
        print("State file not found.")
        return
        
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    if not os.path.exists(APPS_DIR):
        print(f"Apps directory not found: {APPS_DIR}")
        return
    
    # Get list of app directories
    app_dirs = [d for d in os.listdir(APPS_DIR) if os.path.isdir(os.path.join(APPS_DIR, d))]
    
    print(f"Found {len(app_dirs)} app directories")
    
    updated_count = 0
    
    for app_name in app_dirs:
        if app_name not in state:
            continue
            
        commit_count = get_commit_count(app_name)
        
        if commit_count is not None:
            old_count = state[app_name].get('commits', 0)
            state[app_name]['commits'] = commit_count
            
            if old_count != commit_count:
                print(f"{app_name}: {old_count} → {commit_count} commits")
                updated_count += 1
    
    # Save updated state
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"\nUpdated commit counts for {updated_count} apps.")

if __name__ == "__main__":
    main()














