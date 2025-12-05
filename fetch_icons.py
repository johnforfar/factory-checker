import json
import os
import subprocess
import concurrent.futures
import time
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_PUBLIC_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

# User agents
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def fetch_icon(app_name):
    # Check if icon already exists
    app_dir = os.path.join(APPS_PUBLIC_DIR, app_name)
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
        
    icon_path = os.path.join(app_dir, "logo.png")
    if os.path.exists(icon_path):
        return app_name, "Exists"

    # Random delay
    time.sleep(random.uniform(0.5, 1.5))
    
    url = f"https://raw.githubusercontent.com/miniapp-factory/{app_name}/main/mini-app/public/logo.png"
    ua = random.choice(USER_AGENTS)
    
    try:
        # Use curl to download
        cmd = ["curl", "-s", "-H", f"User-Agent: {ua}", "--max-time", "10", "-o", icon_path, url]
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            # Check if file is empty or valid image (not 404 html)
            if os.path.getsize(icon_path) < 1000: # Too small, probably 404 text
                # Check content
                with open(icon_path, 'rb') as f:
                    header = f.read(10)
                if b'404' in header or b'Not Found' in header:
                    os.remove(icon_path)
                    return app_name, "404"
            
            return app_name, "Downloaded"
        else:
            return app_name, "Error"
            
    except Exception as e:
        return app_name, f"Exception: {e}"

def main():
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
        
    apps_to_fetch = [app for app, data in state.items() if data.get('status') != 'Default'] # Skip known defaults if we want speed
    print(f"Fetching icons for {len(apps_to_fetch)} apps...")
    
    downloaded = 0
    existing = 0
    errors = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_app = {executor.submit(fetch_icon, app): app for app in apps_to_fetch}
        
        processed = 0
        for future in concurrent.futures.as_completed(future_to_app):
            app_name = future_to_app[future]
            processed += 1
            try:
                name, result = future.result()
                if result == "Downloaded":
                    downloaded += 1
                    print(f"[{processed}/{len(apps_to_fetch)}] {name}: Downloaded")
                elif result == "Exists":
                    existing += 1
                else:
                    errors += 1
                    # print(f"[{processed}/{len(apps_to_fetch)}] {name}: {result}")
            except Exception as exc:
                print(f"{app_name} exception: {exc}")

    print(f"Finished. Downloaded: {downloaded}, Existing: {existing}, Errors: {errors}")

if __name__ == "__main__":
    main()














