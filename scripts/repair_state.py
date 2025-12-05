import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
BACKUP_FILE = STATE_FILE + ".bak"

def repair():
    if not os.path.exists(STATE_FILE):
        print("No state file.")
        return

    # Backup first
    os.system(f"cp {STATE_FILE} {BACKUP_FILE}")
    
    with open(STATE_FILE, 'r', errors='ignore') as f:
        content = f.read()
        
    # Try to find valid JSON objects using regex or just parse line by line?
    # The file is a big dict: { "app": {...}, ... }
    
    # Regex to find "key": { ... } patterns
    # This is tricky for nested braces.
    
    # Alternative: Read CSV to get master list, then try to extract status for each from the corrupted file.
    
    from csv import DictReader
    csv_file = os.path.join(BASE_DIR, "app-review", "apps.csv")
    
    new_state = {}
    
    # Initialize from CSV
    if os.path.exists(csv_file):
        with open(csv_file, 'r') as f:
            reader = DictReader(f)
            for row in reader:
                new_state[row['name']] = {
                    "last_assessed_hash": row.get('commit_hash', ''),
                    "last_updated": row.get('last_updated_date', ''),
                    "title": row['title'],
                    "status": row['status'],
                    "repo_url": row['repo_url'],
                    "landing_url": row['landing_url']
                }
    
    # Now scrape the corrupted file for "status": "Default" or "last_checked"
    # pattern: "appname": { ... }
    
    # We can try to regex search for specific app entries
    count_recovered = 0
    
    for app_name in new_state:
        # Look for this app block in the content
        # "app_name": { ... }
        # We look for the status line inside the block
        
        # Simple regex for status
        # "app_name":\s*\{[^}]*"status":\s*"([^"]+)"
        
        pattern = f'"{re.escape(app_name)}":\s*\{{[^}}]*"status":\s*"([^"]+)"'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            new_state[app_name]['status'] = match.group(1)
            
        # Recover title if changed
        pattern_title = f'"{re.escape(app_name)}":\s*\{{[^}}]*"title":\s*"([^"]+)"'
        match_title = re.search(pattern_title, content, re.DOTALL)
        if match_title:
            new_state[app_name]['title'] = match_title.group(1)
            
        # Recover last_checked
        pattern_checked = f'"{re.escape(app_name)}":\s*\{{[^}}]*"last_checked":\s*"([^"]+)"'
        match_checked = re.search(pattern_checked, content, re.DOTALL)
        if match_checked:
            new_state[app_name]['last_checked'] = match_checked.group(1)
            count_recovered += 1

    with open(STATE_FILE, 'w') as f:
        json.dump(new_state, f, indent=2)
        
    print(f"Repaired state file. Recovered data for {count_recovered} apps.")

if __name__ == "__main__":
    repair()














