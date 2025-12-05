#!/usr/bin/env python3
"""
Run full updates on apps marked with needs_full_update: true
"""
import json
import os
import subprocess
import sys
import time
import random
import concurrent.futures
import re
from typing import List
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "apps")
APPS_PUBLIC_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_apps_needing_update() -> List[str]:
    """Get list of apps marked for full update"""
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    apps_needing_update = [
        app_name for app_name, app_data in state.items()
        if app_data.get('needs_full_update', False)
    ]
    
    return apps_needing_update

def update_commits(app_names: List[str]):
    """Update commit counts for specified apps"""
    print(f"\n{'='*70}")
    print(f"UPDATING COMMITS ({len(app_names)} apps)")
    print(f"{'='*70}")
    
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    APPS_DIR = os.path.join(BASE_DIR, "apps")
    updated_count = 0
    
    for app_name in app_names:
        repo_path = os.path.join(APPS_DIR, app_name)
        git_dir = os.path.join(repo_path, ".git")
        
        if not os.path.exists(git_dir):
            continue
        
        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "rev-list", "--count", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                commit_count = int(result.stdout.strip())
                old_count = state[app_name].get('commits', 0)
                state[app_name]['commits'] = commit_count
                
                if old_count != commit_count:
                    print(f"  {app_name}: {old_count} → {commit_count} commits")
                    updated_count += 1
        except Exception as e:
            print(f"  Error updating {app_name}: {e}")
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"\n✓ Updated commit counts for {updated_count} apps")

def extract_all_prompts_from_history(content):
    """Extract all prompts from aider chat history"""
    prompts = []
    lines = content.split('\n')
    current_prompt = None
    
    for line in lines:
        if line.startswith('## '):
            # Save previous prompt if exists
            if current_prompt:
                prompts.append({'type': 'Initial', 'text': current_prompt.strip()})
            current_prompt = line[3:].strip()
        elif current_prompt and line.strip():
            current_prompt += '\n' + line
    
    # Save last prompt
    if current_prompt:
        prompts.append({'type': 'Initial', 'text': current_prompt.strip()})
    
    return prompts if prompts else None

def fetch_prompt_history(app_name):
    """Fetch prompt history for a single app"""
    time.sleep(random.uniform(1.0, 2.5))
    
    url = f"https://raw.githubusercontent.com/miniapp-factory/{app_name}/main/.aider.chat.history.md"
    ua = random.choice(USER_AGENTS)
    
    try:
        cmd = ["curl", "-s", "-H", f"User-Agent: {ua}", "--max-time", "10", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return app_name, None, "Error"
            
        content = result.stdout
        
        if not content or "404" in content or "Not Found" in content:
            return app_name, None, "Not Found"
        
        prompts = extract_all_prompts_from_history(content)
        
        if prompts:
            return app_name, prompts, "Success"
        else:
            return app_name, None, "No Prompt Found"
            
    except Exception as e:
        return app_name, None, f"Exception: {e}"

def update_prompts(app_names: List[str]):
    """Update prompt history for specified apps"""
    print(f"\n{'='*70}")
    print(f"UPDATING PROMPTS ({len(app_names)} apps)")
    print(f"{'='*70}")
    
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_app = {executor.submit(fetch_prompt_history, app): app for app in app_names}
        
        for future in concurrent.futures.as_completed(future_to_app):
            app_name = future_to_app[future]
            try:
                name, prompts, status = future.result()
                if status == "Success" and prompts:
                    state[name]['prompts'] = prompts
                    state[name]['prompt'] = prompts[0]['text'] if prompts else None
                    count += 1
                    print(f"  [{count}] {name}: Found {len(prompts)} prompt(s)")
                elif status == "Not Found":
                    pass
                    
                if count % 10 == 0:
                    with open(STATE_FILE, 'w') as f:
                        json.dump(state, f, indent=2)
                        
            except Exception as exc:
                print(f"  {app_name} exception: {exc}")
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"\n✓ Updated prompts for {count} apps")

def fetch_icon(app_name):
    """Fetch icon for a single app"""
    app_dir = os.path.join(APPS_PUBLIC_DIR, app_name)
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
        
    icon_path = os.path.join(app_dir, "logo.png")
    if os.path.exists(icon_path):
        return app_name, "Exists"

    time.sleep(random.uniform(0.5, 1.5))
    
    url = f"https://raw.githubusercontent.com/miniapp-factory/{app_name}/main/mini-app/public/logo.png"
    ua = random.choice(USER_AGENTS)
    
    try:
        cmd = ["curl", "-s", "-H", f"User-Agent: {ua}", "--max-time", "10", "-o", icon_path, url]
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            if os.path.getsize(icon_path) < 1000:
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

def update_icons(app_names: List[str]):
    """Update icons for specified apps"""
    print(f"\n{'='*70}")
    print(f"UPDATING ICONS ({len(app_names)} apps)")
    print(f"{'='*70}")
    
    downloaded = 0
    existing = 0
    errors = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_app = {executor.submit(fetch_icon, app): app for app in app_names}
        
        processed = 0
        for future in concurrent.futures.as_completed(future_to_app):
            app_name = future_to_app[future]
            processed += 1
            try:
                name, result = future.result()
                if result == "Downloaded":
                    downloaded += 1
                    print(f"  [{processed}/{len(app_names)}] {name}: Downloaded")
                elif result == "Exists":
                    existing += 1
                else:
                    errors += 1
            except Exception as exc:
                print(f"  {app_name} exception: {exc}")
    
    print(f"\n✓ Downloaded {downloaded} icons, {existing} already existed, {errors} errors")

def clear_update_flags(app_names: List[str]):
    """Clear needs_full_update flags after successful update"""
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    for app_name in app_names:
        if app_name in state:
            state[app_name]['needs_full_update'] = False
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"✓ Cleared update flags for {len(app_names)} apps")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run full updates on marked apps')
    parser.add_argument('--skip-commits', action='store_true', help='Skip commit updates')
    parser.add_argument('--skip-prompts', action='store_true', help='Skip prompt updates')
    parser.add_argument('--skip-icons', action='store_true', help='Skip icon updates')
    parser.add_argument('--skip-screenshots', action='store_true', help='Skip screenshot processing')
    parser.add_argument('--clear-flags', action='store_true', help='Clear needs_full_update flags after update')
    
    args = parser.parse_args()
    
    apps_needing_update = get_apps_needing_update()
    
    if not apps_needing_update:
        print("No apps marked for full update!")
        return
    
    print(f"\n{'='*70}")
    print(f"FULL UPDATE FOR {len(apps_needing_update)} APPS")
    print(f"{'='*70}")
    print(f"Apps: {', '.join(apps_needing_update[:10])}{'...' if len(apps_needing_update) > 10 else ''}")
    
    # Update commits
    if not args.skip_commits:
        update_commits(apps_needing_update)
    
    # Update prompts
    if not args.skip_prompts:
        update_prompts(apps_needing_update)
    
    # Update icons
    if not args.skip_icons:
        update_icons(apps_needing_update)
    
    # Screenshots - note: continue_screenshot_processing.py handles apps needing screenshots
    if not args.skip_screenshots:
        print(f"\n{'='*70}")
        print(f"SCREENSHOTS")
        print(f"{'='*70}")
        print("Note: Run 'python3 continue_screenshot_processing.py' to process screenshots")
        print("      It will automatically process apps needing screenshots")
    
    # Clear flags if requested
    if args.clear_flags:
        clear_update_flags(apps_needing_update)
    
    print(f"\n{'='*70}")
    print("UPDATE COMPLETE")
    print(f"{'='*70}")
    print(f"Processed {len(apps_needing_update)} apps")
    print("Next: Run 'python3 generate_app_descriptions.py' to update CSV descriptions")
    print("      Run 'python3 continue_screenshot_processing.py' for screenshots")
    print(f"{'='*70}\n")
    apps_needing_update = get_apps_needing_update()
    
    if not apps_needing_update:
        print("No apps marked for full update!")
        return
    
    print(f"\n{'='*70}")
    print(f"FULL UPDATE FOR {len(apps_needing_update)} APPS")
    print(f"{'='*70}")
    print(f"Apps: {', '.join(apps_needing_update[:10])}{'...' if len(apps_needing_update) > 10 else ''}")
    
    # Update commits
    update_commits(apps_needing_update)
    
    print(f"\n{'='*70}")
    print("NEXT STEPS:")
    print(f"{'='*70}")
    print("Run these scripts to complete the full update:")
    print(f"  1. python3 fetch_prompt_history.py  # (modify to filter apps)")
    print(f"  2. python3 continue_screenshot_processing.py  # (processes apps needing screenshots)")
    print(f"  3. python3 fetch_icons.py  # (modify to filter apps)")
    print(f"  4. python3 generate_app_descriptions.py  # (updates CSV)")
    print(f"\nOr run individual update scripts manually for these {len(apps_needing_update)} apps")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()

