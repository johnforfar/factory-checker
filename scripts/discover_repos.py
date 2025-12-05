import csv
import os
import subprocess
import time
import re
from bs4 import BeautifulSoup

ORG_NAME = "miniapp-factory"

def fetch_all_repos():
    page = 1
    all_repos = set()
    
    while True:
        print(f"Fetching page {page}...")
        # Use curl with User-Agent to fetch the profile repositories tab
        url = f"https://github.com/{ORG_NAME}?page={page}&tab=repositories"
        cmd = [
            "curl", 
            "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "-s", 
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error fetching page {page}")
            break
            
        if "Not Found" in result.stdout:
             print("Got 'Not Found' response.")
             break
            
        soup = BeautifulSoup(result.stdout, 'html.parser')
        
        # Look for repository links in the profile view
        # <a href="/miniapp-factory/repo-name" itemprop="name codeRepository">
        repo_links = soup.find_all('a', itemprop="name codeRepository")
        
        if not repo_links:
            # Fallback: look for any link starting with /miniapp-factory/ that isn't a tab/sorting link
            # This is looser but catches things if classes change
            links = soup.find_all('a', href=re.compile(f"^/{ORG_NAME}/[^/]+$"))
            repo_links = [l for l in links if 'tab=' not in l['href']]
            
        current_page_repos = []
        for link in repo_links:
            href = link['href']
            # href is like /miniapp-factory/repo-name
            parts = href.strip('/').split('/')
            if len(parts) == 2 and parts[0] == ORG_NAME:
                repo_name = parts[1]
                if repo_name not in ['miniapp-factory', 'miniapp-factory-frontend', 'miniapp-factory-template', 'miniapp-factory-imagegen', 'miniapp-factory-coder']:
                    current_page_repos.append(repo_name)

        if not current_page_repos:
            print("No new repos found on this page (end of list?).")
            break
            
        print(f"Found {len(current_page_repos)} repos on page {page}")
        for r in current_page_repos:
            all_repos.add(r)
            
        page += 1
        time.sleep(1) # Be nice
        
    return sorted(list(all_repos))

def update_csv(repos):
    csv_file = "app-review/apps.csv"
    existing_data = {}  # Store full row data, not just names
    
    # Handle running from subdir
    if not os.path.exists("app-review"):
        if os.path.exists("../app-review"):
            csv_file = "../app-review/apps.csv"
    
    # Read existing CSV data and get all fieldnames
    fieldnames = None
    if os.path.exists(csv_file):
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames  # Use existing fieldnames
            for row in reader:
                existing_data[row['name']] = row
    
    # If no existing CSV, use default fieldnames
    if not fieldnames:
        fieldnames = ['name', 'title', 'status', 'last_updated_date', 'commit_hash', 'repo_url', 'landing_url']
    
    # Write all repos to CSV (preserve existing data, add missing ones)
    new_count = 0
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for repo in repos:
            if repo in existing_data:
                # Preserve existing row data, but ensure all fields are present
                row = existing_data[repo].copy()
                # Fill in any missing fields with defaults
                for field in fieldnames:
                    if field not in row:
                        row[field] = ''
                writer.writerow(row)
            else:
                # Add new repo with all required fields
                new_row = {field: '' for field in fieldnames}  # Initialize all fields
                new_row['name'] = repo
                new_row['title'] = repo.replace('-', ' ').title()
                new_row['status'] = 'Pending'
                if 'repo_url' in fieldnames:
                    new_row['repo_url'] = f"https://github.com/{ORG_NAME}/{repo}"
                if 'landing_url' in fieldnames:
                    new_row['landing_url'] = f"https://{repo}.{ORG_NAME}.marketplace.openxai.network"
                writer.writerow(new_row)
                new_count += 1
    
    removed_count = len(existing_data) - len(repos)
    if removed_count > 0:
        print(f"Removed {removed_count} apps that no longer exist in GitHub")
    print(f"Added {new_count} new apps to {csv_file}")
    print(f"Total apps in CSV: {len(repos)}")

if __name__ == "__main__":
    repos = fetch_all_repos()
    print(f"Total unique repos found: {len(repos)}")
    update_csv(repos)
