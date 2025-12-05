from bs4 import BeautifulSoup
import csv
import os
import re

CSV_FILE = "app-review/apps.csv"

def load_existing_apps():
    if not os.path.exists(CSV_FILE):
        return set()
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        return {row['name'] for row in reader}

def append_apps(new_apps):
    file_exists = os.path.exists(CSV_FILE)
    existing = load_existing_apps()
    
    # Define columns
    fieldnames = ['name', 'title', 'status', 'last_updated_date', 'commit_hash', 'repo_url', 'landing_url']
    
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
            
        for app in new_apps:
            if app['name'] not in existing:
                writer.writerow({
                    'name': app['name'],
                    'title': app['title'],
                    'status': 'Pending', # Initial status
                    'last_updated_date': '',
                    'commit_hash': '',
                    'repo_url': f"https://github.com/miniapp-factory/{app['name']}",
                    'landing_url': f"https://{app['name']}.miniapp-factory.marketplace.openxai.network"
                })
                existing.add(app['name'])
                print(f"Added new app: {app['name']}")

def extract_apps():
    if not os.path.exists("marketplace.html"):
        print("marketplace.html not found. Please curl it first.")
        return

    with open("marketplace.html", "r") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    apps = []
    
    seen = set()

    for link in soup.find_all("a"):
        href = link.get("href")
        text = link.get_text().strip()
        
        if not href: continue
        
        # Pattern: https://[name].miniapp-factory...
        if "miniapp-factory.marketplace.openxai.network" in href:
            match = re.search(r"https://(.*?)\.miniapp-factory", href)
            if match:
                slug = match.group(1)
                if slug not in ["www", "marketplace", "chatgpt"] and slug not in seen:
                    # Clean title
                    title = text if len(text) > 2 else slug.replace("-", " ").title()
                    apps.append({"name": slug, "title": title})
                    seen.add(slug)
                    
    print(f"Found {len(apps)} apps in marketplace HTML.")
    append_apps(apps)

if __name__ == "__main__":
    extract_apps()
