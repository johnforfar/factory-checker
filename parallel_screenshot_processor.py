#!/usr/bin/env python3
"""
Parallel screenshot processor using Playwright with multiprocessing.
This script processes multiple apps simultaneously for faster screenshot capture.
"""
import json
import os
import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import subprocess
import shutil

# Try to import playwright, install if needed
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright not installed. Install with: pip install playwright && playwright install chromium")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

# Configuration
MAX_WORKERS = 5  # Number of parallel browser instances
PAGE_LOAD_TIMEOUT = 8000  # 8 seconds in milliseconds (reduced from 10)
NAVIGATION_TIMEOUT = 12000  # 12 seconds in milliseconds (reduced from 15)
DYNAMIC_CONTENT_WAIT = 1500  # 1.5 seconds for dynamic content (reduced from 2)
SCREENSHOT_WIDTH = 1280
SCREENSHOT_HEIGHT = 720

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

def take_screenshot_playwright(app_name, url, browser_context):
    """Take a screenshot for a single app using Playwright"""
    try:
        # Create a new page in the browser context
        page = browser_context.new_page()
        
        # Set viewport size
        page.set_viewport_size({"width": SCREENSHOT_WIDTH, "height": SCREENSHOT_HEIGHT})
        
        # Navigate to the URL with timeout
        try:
            page.goto(url, wait_until="networkidle", timeout=NAVIGATION_TIMEOUT)
        except PlaywrightTimeoutError:
            # If networkidle times out, try with load state
            try:
                page.goto(url, wait_until="load", timeout=NAVIGATION_TIMEOUT)
                # Wait a bit for dynamic content (reduced wait time)
                page.wait_for_timeout(DYNAMIC_CONTENT_WAIT)
            except PlaywrightTimeoutError:
                print(f"  ⚠️  {app_name}: Navigation timeout")
                page.close()
                return False, "timeout"
        
        # Wait for page to be ready (check for common loading indicators)
        try:
            # Wait for body to be visible
            page.wait_for_selector("body", timeout=3000)  # Reduced timeout
            # Additional wait for dynamic content (reduced)
            page.wait_for_timeout(500)  # 0.5 seconds for any animations/transitions
        except PlaywrightTimeoutError:
            pass  # Continue anyway
        
        # Create app directory
        app_dir = os.path.join(APPS_DIR, app_name)
        os.makedirs(app_dir, exist_ok=True)
        
        # Take screenshot
        screenshot_path = os.path.join(app_dir, "screenshot-1.png")
        page.screenshot(path=screenshot_path, full_page=False)
        
        # Close page
        page.close()
        
        # Verify screenshot was created and has content
        if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 1000:
            return True, "success"
        else:
            return False, "empty_screenshot"
            
    except Exception as e:
        print(f"  ❌ {app_name}: Error - {str(e)}")
        try:
            page.close()
        except:
            pass
        return False, str(e)

def process_batch_parallel(apps_batch, worker_id):
    """Process a batch of apps in parallel using a single browser instance"""
    results = []
    
    try:
        with sync_playwright() as p:
            # Launch browser (one per worker)
            browser = p.chromium.launch(headless=True)
            browser_context = browser.new_context(
                viewport={"width": SCREENSHOT_WIDTH, "height": SCREENSHOT_HEIGHT},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            
            for app_name, url, status in apps_batch:
                print(f"  📸 [{worker_id}] Processing {app_name}...")
                success, reason = take_screenshot_playwright(app_name, url, browser_context)
                
                if success:
                    print(f"  ✅ [{worker_id}] {app_name}: Screenshot saved")
                    results.append((app_name, True, "success"))
                else:
                    print(f"  ❌ [{worker_id}] {app_name}: Failed ({reason})")
                    results.append((app_name, False, reason))
            
            browser.close()
            
    except Exception as e:
        print(f"  ❌ [{worker_id}] Browser error: {str(e)}")
        for app_name, _, _ in apps_batch:
            results.append((app_name, False, f"browser_error: {str(e)}"))
    
    return results

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

def create_thumbnail(screenshot_path):
    """Create a thumbnail for the screenshot"""
    try:
        from PIL import Image
        
        thumb_path = screenshot_path.replace('.png', '-thumb.png')
        if os.path.exists(thumb_path):
            return  # Already exists
        
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
        print(f"  ⚠️  Thumbnail creation failed: {str(e)}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Parallel screenshot processor')
    parser.add_argument('--batch-size', type=int, default=20, help='Number of apps to process')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help='Number of parallel workers')
    parser.add_argument('--no-pending', action='store_true', help='Exclude pending apps')
    parser.add_argument('--skip-thumbnails', action='store_true', help='Skip thumbnail creation')
    parser.add_argument('--update-state', action='store_true', help='Update last_checked in state file')
    args = parser.parse_args()
    
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Error: Playwright is not installed.")
        print("Install with: pip install playwright && playwright install chromium")
        sys.exit(1)
    
    # Get apps needing screenshots
    apps = get_apps_needing_screenshots(include_pending=not args.no_pending, limit=args.batch_size)
    
    if not apps:
        print("✅ No apps need screenshots!")
        return
    
    print(f"\n{'='*70}")
    print(f"PARALLEL SCREENSHOT PROCESSOR")
    print(f"{'='*70}")
    print(f"Total apps to process: {len(apps)}")
    print(f"Parallel workers: {args.workers}")
    print(f"Including pending: {not args.no_pending}")
    print(f"{'='*70}\n")
    
    # Split apps into batches for each worker
    apps_per_worker = len(apps) // args.workers
    if apps_per_worker == 0:
        apps_per_worker = 1
    
    batches = []
    for i in range(0, len(apps), apps_per_worker):
        batches.append(apps[i:i + apps_per_worker])
    
    # Process batches in parallel
    start_time = time.time()
    successful_apps = []
    failed_apps = []
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_batch_parallel, batch, worker_id): batch
            for worker_id, batch in enumerate(batches, 1)
        }
        
        for future in as_completed(futures):
            batch_results = future.result()
            for app_name, success, reason in batch_results:
                if success:
                    successful_apps.append(app_name)
                    # Create thumbnail
                    if not args.skip_thumbnails:
                        screenshot_path = os.path.join(APPS_DIR, app_name, "screenshot-1.png")
                        if os.path.exists(screenshot_path):
                            create_thumbnail(screenshot_path)
                else:
                    failed_apps.append((app_name, reason))
    
    elapsed_time = time.time() - start_time
    
    # Update state file
    if args.update_state and successful_apps:
        updated = update_last_checked(successful_apps)
        print(f"\n✅ Updated last_checked for {updated} apps")
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"✅ Successful: {len(successful_apps)}")
    print(f"❌ Failed: {len(failed_apps)}")
    print(f"⏱️  Time elapsed: {elapsed_time:.1f} seconds")
    print(f"⚡ Average: {elapsed_time/len(apps):.1f} seconds per app")
    print(f"{'='*70}\n")
    
    if failed_apps:
        print("Failed apps:")
        for app_name, reason in failed_apps[:10]:
            print(f"  ❌ {app_name}: {reason}")
        if len(failed_apps) > 10:
            print(f"  ... and {len(failed_apps) - 10} more")

if __name__ == "__main__":
    main()

