import json
import csv
import os
import time

STATE_FILE = "app-review/apps-state.json"
CSV_FILE = "app-review/apps-report.csv"

def export_to_csv():
    if not os.path.exists(STATE_FILE):
        print("No state file found.")
        return

    with open(STATE_FILE, 'r') as f:
        state = json.load(f)

    # Define columns
    fieldnames = ['name', 'title', 'status', 'last_updated_date', 'commit_hash', 'repo_url']

    with open(CSV_FILE, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for app_name, data in state.items():
            writer.writerow({
                'name': app_name,
                'title': data.get('title', 'Unknown'),
                'status': data.get('status', 'Unknown'),
                'last_updated_date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('last_updated', 0))) if data.get('last_updated') else 'N/A',
                'commit_hash': data.get('last_assessed_hash', 'N/A'),
                'repo_url': f"https://github.com/miniapp-factory/{app_name}"
            })
    
    print(f"Exported {len(state)} apps to {CSV_FILE}")

if __name__ == "__main__":
    export_to_csv()














