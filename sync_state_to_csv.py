#!/usr/bin/env python3
"""
Sync apps-state.json to apps.csv with all data fields including rank.
"""
import json
import csv
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
CSV_FILE = os.path.join(BASE_DIR, "app-review", "apps.csv")
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

def calculate_quality_score(app_data, app_name):
    """Calculate quality score for ranking"""
    import math
    
    score = 0
    commits = app_data.get('commits', 0) or 0
    score += min(math.log10(commits + 1) * 20, 50)
    
    status = app_data.get('status', 'Pending')
    if status == 'Active':
        score += 30
    elif status == 'Default':
        score += 10
    
    # Check for screenshots
    app_path = os.path.join(APPS_DIR, app_name)
    has_screenshots = False
    has_icon = False
    if os.path.exists(app_path):
        files = os.listdir(app_path)
        screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
        has_screenshots = len(screenshots) > 0
        has_icon = any('icon' in f.lower() or 'logo' in f.lower() for f in files if f.endswith('.png'))
    
    if has_screenshots:
        score += 15
        
        # Add visual quality bonus from screenshot analysis (0-25 points)
        screenshot_analysis = app_data.get('screenshot_analysis', {})
        if screenshot_analysis and screenshot_analysis.get('visual_quality') is not None:
            visual_quality = screenshot_analysis.get('visual_quality', 0)
            score += round((visual_quality / 100) * 25)  # Scale 0-100 to 0-25 points
            
            # Bonus for custom content (not default template)
            if screenshot_analysis.get('has_custom_content') == True:
                score += 5
    
    if has_icon:
        score += 10
    
    if app_data.get('description') and app_data.get('description', '').strip():
        score += 10
    
    prompts = app_data.get('prompts') or (app_data.get('prompt') and [{'text': app_data.get('prompt')}])
    if prompts and len(prompts) > 0:
        score += 10
    
    # Recent update bonus
    if app_data.get('last_updated'):
        try:
            if isinstance(app_data['last_updated'], str):
                date = datetime.fromisoformat(app_data['last_updated'].replace('Z', '+00:00'))
            else:
                date = datetime.fromtimestamp(app_data['last_updated'] if app_data['last_updated'] < 946684800000 else app_data['last_updated'] / 1000)
            days = (datetime.now() - date.replace(tzinfo=None)).days
            if days < 7:
                score += 10
            elif days < 30:
                score += 5
            elif days < 90:
                score += 2
        except:
            pass
    
    if app_data.get('last_checked') and app_data.get('last_checked') != 'Never':
        score += 5
    
    return score

def sync_to_csv():
    """Sync state to CSV with all fields"""
    if not os.path.exists(STATE_FILE):
        print(f"State file not found: {STATE_FILE}")
        return
    
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    # Calculate quality scores and ranks
    apps_with_scores = []
    for app_name, app_data in state.items():
        score = calculate_quality_score(app_data, app_name)
        apps_with_scores.append({
            'name': app_name,
            'data': app_data,
            'score': score
        })
    
    # Sort by score (descending), then by name
    apps_with_scores.sort(key=lambda x: (-x['score'], x['name']))
    
    # Assign ranks
    for i, app in enumerate(apps_with_scores):
        app['rank'] = i + 1
    
    # Create rank map
    rank_map = {app['name']: app['rank'] for app in apps_with_scores}
    
    # Define CSV columns
    fieldnames = [
        'rank',
        'name',
        'title',
        'status',
        'commits',
        'description',
        'last_updated',
        'last_checked',
        'builder',
        'has_screenshots',
        'has_icon',
        'has_prompts',
        'prompt_count',
        'repo_url',
        'landing_url'
    ]
    
    # Write to CSV
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for app_name, app_data in state.items():
            # Check for screenshots and icon
            app_path = os.path.join(APPS_DIR, app_name)
            has_screenshots = False
            has_icon = False
            if os.path.exists(app_path):
                files = os.listdir(app_path)
                screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
                has_screenshots = len(screenshots) > 0
                has_icon = any('icon' in f.lower() or 'logo' in f.lower() for f in files if f.endswith('.png'))
            
            prompts = app_data.get('prompts') or (app_data.get('prompt') and [{'text': app_data.get('prompt')}])
            prompt_count = len(prompts) if prompts else 0
            
            writer.writerow({
                'rank': rank_map.get(app_name, 9999),
                'name': app_name,
                'title': app_data.get('title', app_name),
                'status': app_data.get('status', 'Pending'),
                'commits': app_data.get('commits', 0) or 0,
                'description': app_data.get('description', '') or '',
                'last_updated': app_data.get('last_updated', '') or '',
                'last_checked': app_data.get('last_checked', '') or '',
                'builder': app_data.get('builder', '') or '',
                'has_screenshots': 'Yes' if has_screenshots else 'No',
                'has_icon': 'Yes' if has_icon else 'No',
                'has_prompts': 'Yes' if prompt_count > 0 else 'No',
                'prompt_count': prompt_count,
                'repo_url': f"https://github.com/miniapp-factory/{app_name}",
                'landing_url': f"https://{app_name}.miniapp-factory.marketplace.openxai.network"
            })
    
    print(f"Synced {len(state)} apps to {CSV_FILE}")
    print(f"Top 10 ranked apps:")
    for app in apps_with_scores[:10]:
        print(f"  {app['rank']:4d}. {app['name']:30s} (score: {app['score']:.1f})")

if __name__ == "__main__":
    sync_to_csv()

