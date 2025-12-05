#!/usr/bin/env python3
import os
import json
import requests
import time

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app-review", "apps-state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_all_github_repos():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/users/miniapp-factory/repos?per_page=100&page={page}"
        print(f"Fetching page {page} of repos...")
        try:
            resp = requests.get(url)
            if resp.status_code != 200:
                print(f"Failed to fetch repos: {resp.status_code} {resp.text}")
                break
            
            data = resp.json()
            if not data:
                break
            
            for repo in data:
                repos.append(repo['name'])
            
            page += 1
            if len(data) < 100:
                break
        except Exception as e:
            print(f"Error fetching repos: {e}")
            break
            
    return repos

if __name__ == "__main__":
    state = load_state()
    repos = get_all_github_repos()
    print(f"Found {len(repos)} repositories on GitHub")
    print(f"Current state file has {len(state)} apps")
    
    # Add any missing repos to state
    added = 0
    for repo_name in repos:
        if repo_name not in state:
            state[repo_name] = {
                "status": "Pending",
                "last_updated": None,
                "last_checked": None
            }
            added += 1
    
    save_state(state)
    print(f"Added {added} new apps to state file")
    print(f"Total apps in state file: {len(state)}")












