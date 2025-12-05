import json
import os
import subprocess
import time
import random
import concurrent.futures
from bs4 import BeautifulSoup
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")

# User agents
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def fetch_details(app_name):
    # Random delay
    time.sleep(random.uniform(1.0, 3.0))
    
    url = f"https://github.com/miniapp-factory/{app_name}"
    ua = random.choice(USER_AGENTS)
    
    commits = 0
    description = None
    
    try:
        cmd = ["curl", "-s", "-H", f"User-Agent: {ua}", "--max-time", "10", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return app_name, "Error", 0, None
            
        soup = BeautifulSoup(result.stdout, 'html.parser')
        
        # Find commits
        # Look for links that contain "commits" text?
        # Or class "d-none d-sm-inline" -> strong
        
        # Strategy 1: Find 'commits' text
        commits_tag = soup.find('span', attrs={"aria-label": "commits"})
        if not commits_tag:
             # Try finding 'commits' in text
             for span in soup.find_all('span'):
                 if 'commits' in span.get_text():
                     strong = span.find_previous('strong')
                     if strong:
                         val = strong.get_text(strip=True).replace(',', '')
                         if val.isdigit():
                             commits = int(val)
                             break
        else:
             parent = commits_tag.parent
             strong = parent.find('strong')
             if strong:
                 commits = int(strong.get_text(strip=True).replace(',', ''))

        # Find description
        # <p class="f4 my-3">
        desc_tag = soup.find('p', class_="f4 my-3")
        if desc_tag:
            description = desc_tag.get_text(strip=True)
            
        return app_name, "Success", commits, description

    except Exception as e:
        print(f"Error {app_name}: {e}")
        return app_name, "Exception", 0, None

def main():
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
        
    # Prioritize Active apps
    apps_to_check = [app for app, data in state.items() if data.get('status') == 'Active']
    # apps_to_check += [app for app, data in state.items() if data.get('status') == 'Pending'][:50] # Sample pending
    
    print(f"Fetching details for {len(apps_to_check)} Active apps...")
    
    count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_app = {executor.submit(fetch_details, app): app for app in apps_to_check}
        
        for future in concurrent.futures.as_completed(future_to_app):
            app_name = future_to_app[future]
            try:
                name, status, commits, description = future.result()
                if status == "Success":
                    state[name]['commits'] = commits
                    if description:
                        state[name]['description'] = description
                    count += 1
                    print(f"Updated {name}: {commits} commits")
                else:
                    print(f"Failed {name}")
                    
                if count % 10 == 0:
                    with open(STATE_FILE, 'w') as f:
                        json.dump(state, f, indent=2)
                        
            except Exception as exc:
                print(f"{app_name} exception: {exc}")

    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

    print(f"Finished. Updated {count} apps.")

if __name__ == "__main__":
    main()














