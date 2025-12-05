#!/usr/bin/env python3
"""
Fix apps that are incorrectly marked as Inactive but actually exist in GitHub
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
CACHE_FILE = os.path.join(BASE_DIR, "app-review", ".github_dates_cache.json")

def main():
    # Load state
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    # Load GitHub repos from cache
    github_repos = set()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
            github_repos = set(cache.get('dates', {}).keys())
    
    if not github_repos:
        print("GitHub cache not found. Run check_github_updates.py first.")
        return
    
    # Find inactive apps
    inactive_apps = [k for k, v in state.items() if v.get('status') == 'Inactive']
    
    # Separate into: actually deleted vs incorrectly marked
    incorrectly_marked = [app for app in inactive_apps if app in github_repos]
    correctly_marked = [app for app in inactive_apps if app not in github_repos]
    
    print(f"Total inactive apps: {len(inactive_apps)}")
    print(f"  Correctly marked (deleted from GitHub): {len(correctly_marked)}")
    print(f"  Incorrectly marked (exist in GitHub): {len(incorrectly_marked)}")
    
    if correctly_marked:
        print(f"\n✓ These are correctly marked as Inactive:")
        for app in sorted(correctly_marked):
            print(f"  - {app}")
    
    if incorrectly_marked:
        print(f"\n⚠ Fixing {len(incorrectly_marked)} apps that exist in GitHub:")
        fixed_count = 0
        for app in sorted(incorrectly_marked):
            # Reset to Pending status (they'll be re-checked)
            old_status = state[app].get('status')
            state[app]['status'] = 'Pending'
            # Clear last_checked so they get re-checked
            state[app]['last_checked'] = 'Never'
            fixed_count += 1
            print(f"  - {app}: {old_status} → Pending")
        
        # Save updated state
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"\n✓ Fixed {fixed_count} apps (marked as Pending for re-check)")
    else:
        print("\n✓ All inactive apps are correctly marked!")

if __name__ == "__main__":
    main()










