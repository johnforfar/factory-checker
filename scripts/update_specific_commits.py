import json
import os
import requests
import time
import sys

STATE_FILE = "app-review/apps-state.json"
GITHUB_API_BASE = "https://api.github.com/repos/miniapp-factory"

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_latest_commit(app_name):
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
        
    try:
        # Use a short timeout to prevent hanging
        url = f"{GITHUB_API_BASE}/{app_name}/commits?per_page=1"
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                commit = data[0]
                message = commit['commit']['message']
                date_str = commit['commit']['author']['date']
                return message, date_str, "success"
        elif response.status_code == 403:
            return None, None, "rate_limited"
        elif response.status_code == 404:
            return None, None, "not_found"
        else:
            return None, None, f"error_{response.status_code}"
            
    except requests.exceptions.Timeout:
        return None, None, "timeout"
    except Exception as e:
        return None, None, f"error_{str(e)}"
    
    return None, None, "unknown"

def main():
    print("Loading state...")
    state = load_state()
    
    # Priority list (Featured apps first)
    priority_apps = [
        'bonfire', 'base-tic-tac-fly', 'base-dash', 'survival-box', 'ai-riddle-rush',
        'do-you-thing', 'flownest', 'kanikani', 'myminiapp', 'fili-food', 
        '169aac15-0af9-4d1c-bc41-dab62c049d78', 'typhoon-preparedness-app', 
        'store-smart-calculator', 'bounty-go', 'omega', 'random-game', 'win', 
        'cyber-hockey', 'number-tapping-sequence', 'unusual-tower-de', 'crypto-shooter'
    ]
    
    # Identify all targets: Priority apps + Active apps missing commits
    targets = []
    
    # Add priority apps first if they need updates
    for app in priority_apps:
        if app in state:
            # Check if commit is missing or empty
            commit = state[app].get('commit')
            if not commit or commit == "N/A":
                targets.append(app)
                
    # Add other active apps missing commits
    for name, data in state.items():
        if name not in targets and data.get('status') == 'Active':
            commit = data.get('commit')
            if not commit or commit == "N/A":
                targets.append(name)
    
    total = len(targets)
    print(f"Found {total} apps needing commit updates.")
    
    if total == 0:
        print("✅ All apps are up to date!")
        return

    updated_count = 0
    consecutive_errors = 0
    
    for i, app_name in enumerate(targets):
        sys.stdout.write(f"[{i+1}/{total}] {app_name}: ")
        sys.stdout.flush()
        
        msg, date, status = get_latest_commit(app_name)
        
        if status == "success":
            state[app_name]['commit'] = msg
            state[app_name]['last_updated'] = date
            state[app_name]['commits'] = 1 # Indicator
            print(f"✓ Updated ({date})")
            updated_count += 1
            consecutive_errors = 0
        elif status == "rate_limited":
            print("⚠️  RATE LIMITED. Stopping.")
            break
        elif status == "not_found":
            print("✗ Not Found (404)")
            consecutive_errors = 0 # Don't stop for 404s
        else:
            print(f"✗ Failed ({status})")
            consecutive_errors += 1
            
        # Stop if too many errors (likely network issue)
        if consecutive_errors >= 10:
            print("\n⚠️  Too many consecutive errors. Stopping to prevent spamming.")
            break
            
        # Save every 20 apps
        if updated_count > 0 and updated_count % 20 == 0:
            save_state(state)
            
        # Smaller delay with token
        time.sleep(0.1)

    save_state(state)
    print(f"\nSummary: Updated {updated_count} apps out of {total} targets.")

if __name__ == "__main__":
    main()
