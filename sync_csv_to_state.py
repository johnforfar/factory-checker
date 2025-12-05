import json
import csv
import os
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
CSV_FILE = os.path.join(BASE_DIR, "app-review", "apps.csv")

def main():
    if not os.path.exists(STATE_FILE):
        state = {}
    else:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)

    new_count = 0
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name']
            if name not in state:
                state[name] = {
                    "last_assessed_hash": "",
                    "last_updated": datetime.datetime.now().isoformat(),
                    "title": row['title'],
                    "status": "Pending",
                    "repo_url": row['repo_url'],
                    "landing_url": row['landing_url']
                }
                new_count += 1

    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
        
    print(f"Synced {new_count} new apps from CSV to state file.")

if __name__ == "__main__":
    main()














