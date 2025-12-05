#!/usr/bin/env python3
"""
Check GitHub Last Updated vs Last Checked and identify apps needing full updates.

This script:
1. Scrapes GitHub repositories page to get last_updated dates
2. Compares GitHub last_updated to last_checked in state file
3. If GitHub last_updated is NEWER than last_checked, marks app for full update
4. Optionally triggers full update process for those apps
"""
import json
import os
import subprocess
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
CACHE_FILE = os.path.join(BASE_DIR, "app-review", ".github_dates_cache.json")
ORG_NAME = "miniapp-factory"
CACHE_MAX_AGE_HOURS = 1  # Refresh cache if older than 1 hour

def load_state() -> Dict:
    """Load the apps state file"""
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state: Dict):
    """Save the apps state file"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def load_cache() -> Tuple[Optional[Dict[str, str]], Optional[datetime]]:
    """Load cached GitHub dates and return (dates_dict, cache_time)"""
    if not os.path.exists(CACHE_FILE):
        return None, None
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
            dates = cache_data.get('dates', {})
            cache_time_str = cache_data.get('timestamp')
            cache_time = parse_datetime(cache_time_str) if cache_time_str else None
            return dates, cache_time
    except Exception as e:
        print(f"Warning: Could not load cache: {e}")
        return None, None

def save_cache(github_dates: Dict[str, str]):
    """Save GitHub dates to cache"""
    try:
        cache_data = {
            'dates': github_dates,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")

def is_cache_valid(cache_time: Optional[datetime]) -> bool:
    """Check if cache is still valid (not too old)"""
    if not cache_time:
        return False
    
    age_hours = (datetime.now(timezone.utc) - cache_time).total_seconds() / 3600
    return age_hours < CACHE_MAX_AGE_HOURS

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse ISO datetime string to timezone-aware datetime object (UTC)"""
    if not dt_str or dt_str in ['Never', 'Unknown', '']:
        return None
    
    try:
        # Handle ISO format: 2023-11-24T10:00:00Z or 2023-11-24T10:00:00+00:00
        # Normalize to UTC timezone-aware datetime
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        
        # Ensure timezone-aware (convert naive to UTC)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC for consistent comparison
            dt = dt.astimezone(timezone.utc)
        
        return dt
    except Exception as e:
        print(f"Warning: Could not parse datetime '{dt_str}': {e}")
        return None

def fetch_github_last_updated_batched(app_names: List[str], batch_size: int = 20) -> Dict[str, str]:
    """
    Fetch GitHub last_updated dates for specific repos in batches.
    Uses individual repo pages which is faster than scraping all repos.
    Returns dict mapping repo_name -> ISO datetime string
    """
    github_dates = {}
    total_batches = (len(app_names) + batch_size - 1) // batch_size
    
    print(f"Fetching GitHub last_updated dates for {len(app_names)} repos in batches of {batch_size}...")
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(app_names))
        batch = app_names[start_idx:end_idx]
        
        print(f"  Batch {batch_num + 1}/{total_batches}: Processing {len(batch)} repos...")
        
        for app_name in batch:
            url = f"https://github.com/{ORG_NAME}/{app_name}"
            cmd = [
                "curl", 
                "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "-s",
                "--max-time", "5",
                url
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
                
                if result.returncode == 0 and "Not Found" not in result.stdout:
                    soup = BeautifulSoup(result.stdout, 'html.parser')
                    
                    # Try multiple methods to find last updated date
                    # Method 1: Find relative-time tag (most common)
                    time_tags = soup.find_all('relative-time')
                    for time_tag in time_tags:
                        if time_tag.has_attr('datetime'):
                            dt = time_tag['datetime']
                            github_dates[app_name] = dt
                            break
                    
                    # Method 2: If not found, look for "Updated" text with relative-time nearby
                    if app_name not in github_dates:
                        # Look for text containing "Updated" followed by relative-time
                        for elem in soup.find_all(string=re.compile(r'Updated', re.I)):
                            parent = elem.parent
                            time_tag = parent.find('relative-time')
                            if time_tag and time_tag.has_attr('datetime'):
                                dt = time_tag['datetime']
                                github_dates[app_name] = dt
                                break
                
                # Small delay to be nice to GitHub
                time.sleep(0.2)
                
            except Exception as e:
                # Skip on error
                pass
        
        # Longer delay between batches
        if batch_num < total_batches - 1:
            time.sleep(1)
    
    print(f"✓ Fetched last_updated dates for {len(github_dates)}/{len(app_names)} repos")
    return github_dates

def fetch_github_last_updated(use_cache: bool = True) -> Dict[str, str]:
    """
    Scrape GitHub repositories page to get last_updated dates for all repos.
    Returns dict mapping repo_name -> ISO datetime string
    Uses cache if available and fresh.
    """
    # Check cache first
    if use_cache:
        cached_dates, cache_time = load_cache()
        if cached_dates and is_cache_valid(cache_time):
            print(f"✓ Using cached GitHub dates (from {cache_time.strftime('%Y-%m-%d %H:%M:%S')} UTC)")
            return cached_dates
    
    github_dates = {}
    page = 1
    
    print(f"Fetching GitHub last_updated dates from {ORG_NAME} repositories...")
    
    while True:
        print(f"  Fetching page {page}...")
        url = f"https://github.com/{ORG_NAME}?page={page}&tab=repositories"
        cmd = [
            "curl", 
            "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "-s", 
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"  Error fetching page {page}")
            break
            
        if "Not Found" in result.stdout:
            print(f"  Got 'Not Found' response (end of pages)")
            break
            
        soup = BeautifulSoup(result.stdout, 'html.parser')
        
        # Find repo items
        repo_list = soup.find_all('li', itemprop="owns")
        if not repo_list:
            # Fallback for other layout
            repo_list = soup.find_all('li', class_="col-12")
            
        if not repo_list:
            print(f"  No repos found on page {page} (end of list)")
            break
        
        found_on_page = 0
        for li in repo_list:
            # Find repo name
            a = li.find('a', itemprop="name codeRepository")
            if not a:
                continue
                
            href = a['href']
            repo_name = href.split('/')[-1]
            
            # Skip non-app repos
            if repo_name in ['miniapp-factory', 'miniapp-factory-frontend', 'miniapp-factory-template', 
                            'miniapp-factory-imagegen', 'miniapp-factory-coder']:
                continue
            
            # Find time
            time_tag = li.find('relative-time')
            if time_tag and time_tag.has_attr('datetime'):
                dt = time_tag['datetime']  # ISO format: 2023-11-24T10:00:00Z
                github_dates[repo_name] = dt
                found_on_page += 1
        
        if found_on_page == 0:
            # Might be end of list or layout change
            if len(repo_list) == 0:
                break
        
        print(f"  Found {found_on_page} repos on page {page}")
        
        page += 1
        time.sleep(1)  # Be nice to GitHub
        
        if page > 35:  # Safety break
            print("  Reached safety limit (35 pages)")
            break
    
    print(f"✓ Fetched last_updated dates for {len(github_dates)} repos")
    
    # Save to cache
    if use_cache:
        save_cache(github_dates)
    
    return github_dates

def compare_dates_and_find_updates(github_dates: Dict[str, str] = None, use_batched: bool = True) -> List[Tuple[str, str, str, str]]:
    """
    Compare GitHub last_updated to last_checked and find apps needing updates.
    Returns list of tuples: (app_name, github_last_updated, last_checked, state_last_updated)
    """
    state = load_state()
    
    # Fetch GitHub dates if not provided
    if github_dates is None:
        if use_batched:
            # Only fetch dates for apps in state file (much faster)
            app_names = list(state.keys())
            github_dates = fetch_github_last_updated_batched(app_names, batch_size=20)
        else:
            # Fetch all repos (slower but comprehensive)
            github_dates = fetch_github_last_updated()
    
    apps_needing_update = []
    
    print(f"\nComparing dates for {len(state)} apps in state file...")
    
    for app_name, app_data in state.items():
        # Skip if app not found in GitHub (might be deleted or renamed)
        if app_name not in github_dates:
            continue
        
        github_last_updated_str = github_dates[app_name]
        last_checked_str = app_data.get('last_checked', 'Never')
        state_last_updated_str = app_data.get('last_updated', 'Never')
        
        github_dt = parse_datetime(github_last_updated_str)
        last_checked_dt = parse_datetime(last_checked_str)
        state_last_updated_dt = parse_datetime(state_last_updated_str)
        
        # If we can't parse GitHub date, skip
        if not github_dt:
            continue
        
        # Check if GitHub last_updated is NEWER than last_checked
        # This means the repo was updated after we last checked it
        needs_update = False
        if not last_checked_dt:
            # Never checked before, needs update
            needs_update = True
        elif github_dt > last_checked_dt:
            # GitHub repo was updated after we last checked
            needs_update = True
        
        if needs_update:
            apps_needing_update.append((app_name, github_last_updated_str, last_checked_str, state_last_updated_str))
    
    return apps_needing_update

def mark_apps_for_update(apps_needing_update: List[Tuple[str, str, str, str]], github_dates: Dict[str, str], update_state: bool = False):
    """
    Mark apps as needing update in state file.
    Optionally update last_updated from GitHub if it's newer.
    """
    if not apps_needing_update:
        print("\n✓ No apps need updates!")
        return
    
    state = load_state()
    
    print(f"\n{'='*70}")
    print(f"APPS NEEDING FULL UPDATE ({len(apps_needing_update)} apps)")
    print(f"{'='*70}")
    
    for app_name, github_last_updated, last_checked, state_last_updated in apps_needing_update:
        if app_name not in state:
            continue
        
        # Update last_updated from GitHub if newer
        if update_state:
            state[app_name]['last_updated'] = github_last_updated
            # Mark that this app needs a full update
            state[app_name]['needs_full_update'] = True
        
        print(f"  {app_name:35s} | GitHub: {github_last_updated:20s} | Last Checked: {last_checked or 'Never':20s} | State Last Updated: {state_last_updated or 'Never':20s}")
    
    if update_state:
        save_state(state)
        print(f"\n✓ Marked {len(apps_needing_update)} apps for full update in state file")
    else:
        print(f"\n⚠ Run with --update-state to mark these apps for update")

def trigger_full_update(app_name: str):
    """
    Trigger a full update for a single app.
    This would involve:
    - Fetching commits (get_commits_from_submodules.py or fetch_details.py)
    - Fetching prompts (fetch_prompt_history.py)
    - Taking screenshots (process_screenshots.py)
    - Fetching icons (fetch_icons.py)
    - Updating metadata (generate_app_descriptions.py)
    
    For now, this just prints what would be done.
    """
    print(f"  Would trigger full update for: {app_name}")
    print(f"    - Fetch commits")
    print(f"    - Fetch prompts")
    print(f"    - Take screenshots")
    print(f"    - Fetch icons")
    print(f"    - Update metadata")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Check GitHub updates and identify apps needing full updates')
    parser.add_argument('--update-state', action='store_true', 
                       help='Update state file with GitHub dates and mark apps for update')
    parser.add_argument('--trigger-updates', action='store_true',
                       help='Trigger full update process for apps needing updates (not implemented yet)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of apps to process')
    parser.add_argument('--batch-size', type=int, default=20,
                       help='Batch size for fetching GitHub dates (default: 20)')
    parser.add_argument('--fetch-all', action='store_true',
                       help='Fetch all repos instead of just apps in state file (slower)')
    parser.add_argument('--no-cache', action='store_true',
                       help='Skip cache and force fresh fetch')
    parser.add_argument('--refresh-cache', action='store_true',
                       help='Force refresh cache even if it exists')
    
    args = parser.parse_args()
    
    # Fetch GitHub dates once
    use_cache = not args.no_cache and not args.refresh_cache
    
    if args.fetch_all:
        github_dates = fetch_github_last_updated(use_cache=use_cache)
    else:
        # For batched mode, check cache first
        if use_cache:
            cached_dates, cache_time = load_cache()
            if cached_dates and is_cache_valid(cache_time):
                print(f"✓ Using cached GitHub dates (from {cache_time.strftime('%Y-%m-%d %H:%M:%S')} UTC)")
                github_dates = cached_dates
            else:
                # Batched fetch - only for apps in state file
                state = load_state()
                app_names = list(state.keys())
                if args.limit:
                    app_names = app_names[:args.limit]
                github_dates = fetch_github_last_updated_batched(app_names, batch_size=args.batch_size)
                # Save to cache
                save_cache(github_dates)
        else:
            # Batched fetch - only for apps in state file
            state = load_state()
            app_names = list(state.keys())
            if args.limit:
                app_names = app_names[:args.limit]
            github_dates = fetch_github_last_updated_batched(app_names, batch_size=args.batch_size)
    
    # Find apps needing updates
    apps_needing_update = compare_dates_and_find_updates(github_dates=github_dates, use_batched=not args.fetch_all)
    
    if args.limit:
        apps_needing_update = apps_needing_update[:args.limit]
    
    # Mark apps for update if requested
    mark_apps_for_update(apps_needing_update, github_dates=github_dates, update_state=args.update_state)
    
    # Trigger updates if requested
    if args.trigger_updates:
        print(f"\n{'='*70}")
        print(f"TRIGGERING FULL UPDATES")
        print(f"{'='*70}")
        for app_name, _, _, _ in apps_needing_update:
            trigger_full_update(app_name)
        print(f"\n⚠ Full update triggering not yet implemented")
        print(f"  Run these scripts manually for each app:")
        print(f"    - python3 get_commits_from_submodules.py")
        print(f"    - python3 fetch_prompt_history.py")
        print(f"    - python3 continue_screenshot_processing.py")
        print(f"    - python3 fetch_icons.py")
        print(f"    - python3 generate_app_descriptions.py")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"Total apps checked: {len(load_state())}")
    print(f"Apps needing update: {len(apps_needing_update)}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()

