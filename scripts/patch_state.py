import json
import os

STATE_FILE = "app-review/apps-state.json"

# Observed titles from browser logs
TITLES = {
    "xos": "Zodiac Quiz",
    "mario": "Emoji Mario Game",
    "quiz": "Animal Quiz",
    "dragon-hunter": "Animal Quiz",
    "alpha": "Mini App Factory App",
    "stonks": "Mini App Factory App"
}

def update_state():
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    for app, data in state.items():
        # Heuristic: If title is "Mini App Factory App", it's Default
        title = TITLES.get(app, "Unknown")
        data['title'] = title
        data['status'] = "Default" if title == "Mini App Factory App" else "Active"
        
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    print("State updated with titles and status.")

if __name__ == "__main__":
    update_state()














