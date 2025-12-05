import json
import os
import subprocess
import time
import re
from bs4 import BeautifulSoup
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
ORG_NAME = "miniapp-factory"

def parse_relative_time(text):
    # "Updated 2 hours ago", "Updated on Apr 5", "Updated yesterday"
    # This is hard to parse perfectly without a library like dateparser.
    # But GitHub HTML usually includes a <relative-time> tag with datetime attribute!
    return text

def fetch_dates():
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
        
    page = 1
    updates_count = 0
    
    while True:
        print(f"Fetching page {page} to update dates...")
        url = f"https://github.com/{ORG_NAME}?page={page}&tab=repositories"
        cmd = [
            "curl", 
            "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "-s", 
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("Error fetching page")
            break
            
        soup = BeautifulSoup(result.stdout, 'html.parser')
        
        # Find repo items
        # <li ... itemprop="owns"> ... <a href="/miniapp-factory/repo" ...> ... <relative-time datetime="2023-11-24T...">
        
        repo_list = soup.find_all('li', itemprop="owns")
        if not repo_list:
            # Fallback for other layout
            repo_list = soup.find_all('li', class_="col-12") # Generic list item in repo tab
            
        if not repo_list:
            print("No repos found on page.")
            break
            
        found_on_page = 0
        for li in repo_list:
            # Find repo name
            a = li.find('a', itemprop="name codeRepository")
            if not a:
                continue
                
            href = a['href']
            repo_name = href.split('/')[-1]
            
            # Find time
            time_tag = li.find('relative-time')
            if time_tag and time_tag.has_attr('datetime'):
                dt = time_tag['datetime'] # ISO format: 2023-11-24T10:00:00Z
                
                if repo_name in state:
                    state[repo_name]['last_updated'] = dt
                    updates_count += 1
                    found_on_page += 1
            else:
                # Try finding text "Updated ..."
                pass

        if found_on_page == 0:
            # Might be end of list or layout change
            # Check if we found ANY repos on this page to decide whether to stop
            if len(repo_list) == 0:
                break
                
        print(f"Updated {found_on_page} apps on page {page}")
        
        # Save periodically
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
            
        page += 1
        time.sleep(1)
        
        if page > 35: # Safety break
            break

    print(f"Finished. Updated dates for {updates_count} apps.")

if __name__ == "__main__":
    fetch_dates()














