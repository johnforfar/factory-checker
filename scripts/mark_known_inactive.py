#!/usr/bin/env python3
"""
Mark known deleted apps as Inactive based on cleanup output
These are apps that were removed from GitHub but we want to preserve in state
"""
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")

# Apps that were removed during cleanup (from cleanup output)
# These should be marked as Inactive if they're added back to state
KNOWN_DELETED_APPS = [
    'ali-ai', 'awuuu', 'bonfire', 'bounty-go', 'brain-box', 'casino', 
    'epistemology', 'evolve', 'falling-sand-game', 'firefly-keeper',
    'food-mines', 'fortune-cookie', 'get-my-meds', 'infinite-ai-trivia',
    'jiji', 'late-for-class', 'little-frog', 'lucky-spin', 'memory-tiles',
    'minesweeper', 'mouse-escape', 'mouse-hunt', 'my-cutesey', 'nikolas',
    'niks', 'omega', 'oracle', 'puzzle', 'random-game', 'rocky',
    'store-smart-calculator', 'the-oracle', 'the-perfect-10',
    'thefoolchemistrywizard', 'typhoon-preparedness-app', 'verifolio',
    'wizard-house-quiz'
]

def main():
    # Load current state
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    # Check which of these apps are currently in state
    in_state = [app for app in KNOWN_DELETED_APPS if app in state]
    not_in_state = [app for app in KNOWN_DELETED_APPS if app not in state]
    
    print(f"Known deleted apps: {len(KNOWN_DELETED_APPS)}")
    print(f"Currently in state: {len(in_state)}")
    print(f"Not in state (were removed): {len(not_in_state)}")
    
    if in_state:
        # Mark any that are in state as Inactive
        marked = 0
        for app in in_state:
            if state[app].get('status') != 'Inactive':
                state[app]['status'] = 'Inactive'
                marked += 1
        
        if marked > 0:
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            print(f"\n✓ Marked {marked} apps as Inactive")
        else:
            print(f"\nAll {len(in_state)} apps already marked as Inactive")
    
    if not_in_state:
        print(f"\n{len(not_in_state)} apps were removed from state and cannot be restored")
        print("Going forward, cleanup_state.py will mark deleted apps as Inactive instead of removing them")

if __name__ == "__main__":
    main()










