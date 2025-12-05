#!/usr/bin/env python3
"""
Robust parallel screenshot processor using Cursor v2 MCP browser tools.
Includes retry logic and network error handling for mobile/unstable connections.
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

# Configuration - optimized for mobile/unstable connections
PAGE_LOAD_WAIT = 3.0  # Increased from 2s for mobile connections
DYNAMIC_CONTENT_WAIT = 1.5  # Additional wait for dynamic content
MAX_RETRIES = 3  # Number of retries for failed requests
RETRY_DELAY = 2.0  # Seconds to wait between retries
BATCH_SIZE = 6  # Process 6 apps in parallel

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def get_apps_needing_screenshots(include_pending=True, limit=None):
    """Get list of apps that need screenshots"""
    state = load_state()
    needs_screenshots = []
    
    for name, data in state.items():
        app_path = os.path.join(APPS_DIR, name)
        has_screenshot = False
        
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            screenshots = [f for f in files if f.endswith('.png') and 
                          'icon' not in f.lower() and 'logo' not in f.lower() and 
                          'thumb' not in f.lower()]
            has_screenshot = len(screenshots) > 0
        
        status = data.get('status', 'Pending')
        
        # Include based on status
        if include_pending or status in ['Active', 'Default']:
            if not has_screenshot:
                url = f"https://{name}.miniapp-factory.marketplace.openxai.network"
                needs_screenshots.append((name, url, status))
    
    if limit:
        needs_screenshots = needs_screenshots[:limit]
    
    return needs_screenshots

def is_network_error(page_title, page_snapshot):
    """Check if page indicates a network error"""
    if not page_title:
        return True
    
    error_indicators = [
        '502',
        '503',
        '504',
        'timeout',
        'bad gateway',
        'service unavailable',
        'gateway timeout',
        'network error',
        'connection error'
    ]
    
    title_lower = page_title.lower()
    for indicator in error_indicators:
        if indicator in title_lower:
            return True
    
    # Check if snapshot is empty or minimal (might indicate error)
    if page_snapshot and isinstance(page_snapshot, dict):
        # Very minimal content might indicate an error page
        if 'children' in page_snapshot:
            children = page_snapshot.get('children', [])
            if len(children) < 2:  # Just header and minimal content
                return True
    
    return False

def create_thumbnail(screenshot_path):
    """Create a thumbnail for the screenshot"""
    try:
        from PIL import Image
        
        thumb_path = screenshot_path.replace('.png', '-thumb.png')
        if os.path.exists(thumb_path):
            return True  # Already exists
        
        img = Image.open(screenshot_path)
        img.thumbnail((400, 300), Image.Resampling.LANCZOS)
        
        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        
        img.save(thumb_path, 'PNG', optimize=True)
        return True
    except Exception as e:
        print(f"  ⚠️  Thumbnail creation failed for {screenshot_path}: {str(e)}")
        return False

def update_last_checked(app_names):
    """Update last_checked timestamp for successfully processed apps"""
    state = load_state()
    updated_count = 0
    
    for app_name in app_names:
        if app_name in state:
            state[app_name]['last_checked'] = datetime.now().isoformat()
            updated_count += 1
    
    if updated_count > 0:
        save_state(state)
    
    return updated_count

def save_screenshot_from_temp(app_name, temp_filename):
    """Save screenshot from temp directory to app directory"""
    temp_dir = "/var/folders/bn/ml8l4wps6770plhr2r14g0dm0000gn/T/cursor/screenshots"
    temp_path = os.path.join(temp_dir, temp_filename)
    app_dir = os.path.join(APPS_DIR, app_name)
    dest_path = os.path.join(app_dir, "screenshot-1.png")
    
    if not os.path.exists(temp_path):
        return False
    
    os.makedirs(app_dir, exist_ok=True)
    try:
        import shutil
        shutil.copy2(temp_path, dest_path)
        
        # Create thumbnail
        create_thumbnail(dest_path)
        
        return True
    except Exception as e:
        print(f"  ❌ Error saving screenshot for {app_name}: {str(e)}")
        return False

def generate_batch_instructions(batch):
    """Generate instructions for processing a batch of apps"""
    print(f"\n{'='*70}")
    print(f"BATCH PROCESSING INSTRUCTIONS (WITH RETRY LOGIC)")
    print(f"{'='*70}")
    print(f"Batch size: {len(batch)} apps")
    print(f"Wait time: {PAGE_LOAD_WAIT}s (optimized for mobile)")
    print(f"Max retries: {MAX_RETRIES}")
    print(f"Retry delay: {RETRY_DELAY}s")
    print(f"{'='*70}\n")
    
    print("Apps in this batch:")
    for i, (app_name, url, status) in enumerate(batch, 1):
        print(f"  {i}. [{status:8s}] {app_name:35s} -> {url}")
    
    print(f"\n{'='*70}")
    print("PROCESSING STEPS (WITH RETRY LOGIC):")
    print(f"{'='*70}")
    print("1. Navigate to all URLs in parallel using browser_navigate")
    print(f"2. Wait {PAGE_LOAD_WAIT} seconds for pages to load")
    print("3. Check for network errors (502, 503, 504, timeout, etc.)")
    print("4. If error detected, retry up to MAX_RETRIES times")
    print("5. Take screenshots for all apps in parallel")
    print("6. Save screenshots and create thumbnails automatically")
    print("7. Update state file")
    print(f"{'='*70}\n")
    
    return batch

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Robust parallel browser screenshot processor with retry logic')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='Number of apps to process per batch')
    parser.add_argument('--no-pending', action='store_true', help='Exclude pending apps')
    parser.add_argument('--update-state', action='store_true', help='Update last_checked in state file')
    parser.add_argument('--list-only', action='store_true', help='Only list apps, do not generate instructions')
    parser.add_argument('--auto-confirm', action='store_true', help='Automatically confirm and proceed between batches')
    args = parser.parse_args()
    
    # Get apps needing screenshots
    apps = get_apps_needing_screenshots(include_pending=not args.no_pending, limit=None)
    
    if not apps:
        print("✅ No apps need screenshots!")
        return
    
    print(f"\n{'='*70}")
    print(f"CURSOR V2 BROWSER TOOLS - ROBUST PARALLEL SCREENSHOT PROCESSOR")
    print(f"{'='*70}")
    print(f"Total apps needing screenshots: {len(apps)}")
    print(f"Batch size: {args.batch_size}")
    print(f"Including pending: {not args.no_pending}")
    print(f"Wait time: {PAGE_LOAD_WAIT}s (optimized for mobile)")
    print(f"Max retries: {MAX_RETRIES}")
    print(f"{'='*70}\n")
    
    if args.list_only:
        print("Apps needing screenshots:")
        for i, (app_name, url, status) in enumerate(apps[:50], 1):
            print(f"  {i:3d}. [{status:8s}] {app_name:35s} -> {url}")
        if len(apps) > 50:
            print(f"  ... and {len(apps) - 50} more apps")
        return
    
    # Process in batches
    total_batches = (len(apps) + args.batch_size - 1) // args.batch_size
    
    print(f"Processing {len(apps)} apps in {total_batches} batches of {args.batch_size}...\n")
    
    for batch_num in range(total_batches):
        start_idx = batch_num * args.batch_size
        end_idx = min(start_idx + args.batch_size, len(apps))
        batch = apps[start_idx:end_idx]
        
        print(f"\n{'='*70}")
        print(f"BATCH {batch_num + 1}/{total_batches}")
        print(f"{'='*70}")
        batch_instructions = generate_batch_instructions(batch)
        
        # Generate the actual batch data for the agent
        print("\nBatch data for agent:")
        print("=" * 70)
        for app_name, url, status in batch:
            print(f"  - {app_name}: {url}")
        print("=" * 70)
        
        if batch_num < total_batches - 1:
            if not args.auto_confirm:
                print("\nPress Enter to continue to next batch, or Ctrl+C to stop...")
                try:
                    input()
                except KeyboardInterrupt:
                    print("\n\nStopped by user.")
                    break
            else:
                 print("\nAuto-confirming next batch...")
                 time.sleep(1)

if __name__ == "__main__":
    main()










