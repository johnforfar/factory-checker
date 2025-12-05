import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

with open(STATE_FILE, 'r') as f:
    state = json.load(f)

needs_screenshot = []
for app, data in state.items():
    if data.get('status') == 'Active':
        app_dir = os.path.join(APPS_DIR, app)
        has_shot = False
        if os.path.exists(app_dir):
            files = os.listdir(app_dir)
            if any(f.endswith('.png') and 'logo' not in f and 'icon' not in f for f in files):
                has_shot = True
        
        if not has_shot:
            needs_screenshot.append(app)

print(f"Apps needing screenshots: {len(needs_screenshot)}")
print("First 10:", needs_screenshot[:10])














