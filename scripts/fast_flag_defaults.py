import json
import os
import subprocess
import concurrent.futures
import time
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")

# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

def check_app(app_name):
    # Random delay to be nice
    time.sleep(random.uniform(0.5, 2.0))
    
    url = f"https://raw.githubusercontent.com/miniapp-factory/{app_name}/main/mini-app/lib/metadata.ts"
    ua = random.choice(USER_AGENTS)
    
    try:
        cmd = ["curl", "-s", "-H", f"User-Agent: {ua}", "--max-time", "10", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # curl failed
            return app_name, "Error", None
            
        content = result.stdout
        
        if not content:
            # Empty response (maybe 404 or block)
            return app_name, "Empty", None

        if 'title = "Mini App Factory App"' in content:
            return app_name, "Default", "Mini App Factory App"
        if 'description = "This app was created by the Mini App Factory!"' in content:
            return app_name, "Default", "Mini App Factory App"
            
        # Try to extract real title if possible
        import re
        title_match = re.search(r'title\s*=\s*["\']([^"\']+)["\']', content)
        if title_match:
             return app_name, "Active", title_match.group(1)
             
        return app_name, "Active", None # Assumed active if not default template
            
    except Exception as e:
        print(f"Error checking {app_name}: {e}")
        return app_name, "Error", None

def main():
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    # Prioritize Pending apps
    pending_apps = [app for app, data in state.items() if data.get('status') == 'Pending']
    # Then check Active ones if we want to double check (optional, skip for now to save calls)
    # pending_apps += [app for app, data in state.items() if data.get('status') == 'Active']
    
    print(f"Checking {len(pending_apps)} Pending apps for default status...")
    
    default_count = 0
    processed = 0
    
    # Reduced concurrency
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_app = {executor.submit(check_app, app): app for app in pending_apps}
        
        for future in concurrent.futures.as_completed(future_to_app):
            app_name = future_to_app[future]
            try:
                name, status, title = future.result()
                processed += 1
                
                import datetime
                current_time = datetime.datetime.now().isoformat()
                
                if status == "Default":
                    state[name]['status'] = "Default"
                    state[name]['title'] = title
                    state[name]['last_checked'] = current_time
                    default_count += 1
                    print(f"[{processed}/{len(pending_apps)}] {name} is DEFAULT")
                elif status == "Active":
                    state[name]['status'] = "Active"
                    state[name]['last_checked'] = current_time
                    if title:
                        state[name]['title'] = title
                    # print(f"[{processed}/{len(pending_apps)}] {name} is Active")
                elif status == "Error" or status == "Empty":
                    # If it failed, maybe don't update last_checked so we retry?
                    # Or update it to show we tried? Let's NOT update last_checked on error so it stays pending retry.
                    print(f"[{processed}/{len(pending_apps)}] {name} failed check (keeping Pending)")
                    
                if processed % 10 == 0:
                    # Save periodically
                    with open(STATE_FILE, 'w') as f:
                        json.dump(state, f, indent=2)
                    print(f"Saved progress. Found {default_count} defaults so far.")
                    
            except Exception as exc:
                print(f'{app_name} generated an exception: {exc}')

    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
        
    print(f"Finished. Flagged {default_count} default apps.")

if __name__ == "__main__":
    main()
