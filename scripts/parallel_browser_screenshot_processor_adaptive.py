#!/usr/bin/env python3
"""
Adaptive parallel screenshot processor using Cursor v2 MCP browser tools.
Implements TCP-like windowing: doubles batch size when stable, reduces when unstable.
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
PAGE_LOAD_WAIT = 3.0  # Wait time for page load
DYNAMIC_CONTENT_WAIT = 1.5  # Additional wait for dynamic content
MAX_RETRIES = 3  # Number of retries for failed requests
RETRY_DELAY = 2.0  # Seconds to wait between retries

# Adaptive windowing configuration
MIN_BATCH_SIZE = 2  # Minimum batch size
MAX_BATCH_SIZE = 64  # Maximum batch size
INITIAL_BATCH_SIZE = 6  # Starting batch size
SUCCESS_THRESHOLD = 0.90  # 90% success rate to increase batch size
STABILITY_WINDOW = 3  # Number of consecutive successful batches before increasing
REDUCE_THRESHOLD = 0.70  # Below 70% success rate, reduce batch size

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
                url = data.get('landing_url')
                if not url:
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

class AdaptiveBatchSizer:
    """Manages adaptive batch sizing based on success rates"""
    def __init__(self):
        self.current_batch_size = INITIAL_BATCH_SIZE
        self.recent_success_rates = []  # Track last N batches
        self.consecutive_successful_batches = 0
        
    def record_batch_result(self, success_count, total_count):
        """Record the result of a batch and adjust batch size"""
        if total_count == 0:
            return
        
        success_rate = success_count / total_count
        self.recent_success_rates.append(success_rate)
        
        # Keep only last STABILITY_WINDOW batches
        if len(self.recent_success_rates) > STABILITY_WINDOW:
            self.recent_success_rates.pop(0)
        
        # Calculate average success rate
        avg_success_rate = sum(self.recent_success_rates) / len(self.recent_success_rates)
        
        # Adjust batch size based on performance
        old_size = self.current_batch_size
        
        if success_rate >= SUCCESS_THRESHOLD:
            self.consecutive_successful_batches += 1
            
            # If we've had STABILITY_WINDOW consecutive successful batches, increase size
            if self.consecutive_successful_batches >= STABILITY_WINDOW:
                if self.current_batch_size < MAX_BATCH_SIZE:
                    self.current_batch_size = min(self.current_batch_size * 2, MAX_BATCH_SIZE)
                    self.consecutive_successful_batches = 0  # Reset counter
                    print(f"\n📈 Batch size increased: {old_size} → {self.current_batch_size} (success rate: {success_rate:.1%})")
        else:
            self.consecutive_successful_batches = 0  # Reset on failure
        
        # Reduce batch size if success rate drops too low
        if success_rate < REDUCE_THRESHOLD:
            if self.current_batch_size > MIN_BATCH_SIZE:
                self.current_batch_size = max(self.current_batch_size // 2, MIN_BATCH_SIZE)
                print(f"\n📉 Batch size reduced: {old_size} → {self.current_batch_size} (success rate: {success_rate:.1%})")
                self.recent_success_rates = []  # Reset history after reduction
        
        return {
            'success_rate': success_rate,
            'avg_success_rate': avg_success_rate,
            'batch_size': self.current_batch_size,
            'old_batch_size': old_size
        }
    
    def get_current_batch_size(self):
        return self.current_batch_size

def generate_batch_instructions(batch, batch_size_info):
    """Generate instructions for processing a batch of apps"""
    current_size = batch_size_info['batch_size']
    success_rate = batch_size_info.get('success_rate', 0)
    
    print(f"\n{'='*70}")
    print(f"ADAPTIVE BATCH PROCESSING (TCP-like windowing)")
    print(f"{'='*70}")
    print(f"Current batch size: {current_size} apps")
    print(f"Last success rate: {success_rate:.1%}" if success_rate > 0 else "Initial batch")
    print(f"Wait time: {PAGE_LOAD_WAIT}s")
    print(f"Max retries: {MAX_RETRIES}")
    print(f"Retry delay: {RETRY_DELAY}s")
    print(f"{'='*70}\n")
    
    print("Apps in this batch:")
    for i, (app_name, url, status) in enumerate(batch, 1):
        print(f"  {i}. [{status:8s}] {app_name:35s} -> {url}")
    
    print(f"\n{'='*70}")
    print("PROCESSING STEPS:")
    print(f"{'='*70}")
    print("1. Navigate to all URLs in parallel using browser_navigate")
    print(f"2. Wait {PAGE_LOAD_WAIT} seconds for pages to load")
    print("3. Check for network errors (502, 503, 504, timeout, etc.)")
    print("4. If error detected, retry up to MAX_RETRIES times")
    print("5. Take screenshots for all apps in parallel")
    print("6. Save screenshots and create thumbnails automatically")
    print("7. Update state file and adjust batch size based on success rate")
    print(f"{'='*70}\n")
    
    return batch

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Adaptive parallel browser screenshot processor with TCP-like windowing')
    parser.add_argument('--initial-batch-size', type=int, default=INITIAL_BATCH_SIZE, 
                       help=f'Initial batch size (default: {INITIAL_BATCH_SIZE})')
    parser.add_argument('--min-batch-size', type=int, default=MIN_BATCH_SIZE,
                       help=f'Minimum batch size (default: {MIN_BATCH_SIZE})')
    parser.add_argument('--max-batch-size', type=int, default=MAX_BATCH_SIZE,
                       help=f'Maximum batch size (default: {MAX_BATCH_SIZE})')
    parser.add_argument('--no-pending', action='store_true', help='Exclude pending apps')
    parser.add_argument('--list-only', action='store_true', help='Only list apps, do not generate instructions')
    args = parser.parse_args()
    
    # Initialize adaptive batch sizer
    batch_sizer = AdaptiveBatchSizer()
    batch_sizer.current_batch_size = args.initial_batch_size
    batch_sizer.current_batch_size = max(MIN_BATCH_SIZE, min(args.max_batch_size, args.initial_batch_size))
    
    # Get apps needing screenshots
    apps = get_apps_needing_screenshots(include_pending=not args.no_pending, limit=None)
    
    if not apps:
        print("✅ No apps need screenshots!")
        return
    
    print(f"\n{'='*70}")
    print(f"ADAPTIVE PARALLEL SCREENSHOT PROCESSOR (TCP-like windowing)")
    print(f"{'='*70}")
    print(f"Total apps needing screenshots: {len(apps)}")
    print(f"Initial batch size: {batch_sizer.current_batch_size}")
    print(f"Batch size range: {args.min_batch_size} - {args.max_batch_size}")
    print(f"Success threshold: {SUCCESS_THRESHOLD:.0%} (to increase)")
    print(f"Reduce threshold: {REDUCE_THRESHOLD:.0%} (to decrease)")
    print(f"Stability window: {STABILITY_WINDOW} batches")
    print(f"Wait time: {PAGE_LOAD_WAIT}s")
    print(f"{'='*70}\n")
    
    if args.list_only:
        print("Apps needing screenshots:")
        for i, (app_name, url, status) in enumerate(apps[:50], 1):
            print(f"  {i:3d}. [{status:8s}] {app_name:35s} -> {url}")
        if len(apps) > 50:
            print(f"  ... and {len(apps) - 50} more apps")
        return
    
    # Process in adaptive batches
    processed = 0
    batch_num = 0
    
    while processed < len(apps):
        current_batch_size = batch_sizer.get_current_batch_size()
        batch = apps[processed:processed + current_batch_size]
        
        if not batch:
            break
        
        batch_num += 1
        remaining = len(apps) - processed
        estimated_batches = remaining / current_batch_size if current_batch_size > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"BATCH {batch_num} | Batch size: {current_batch_size} | Remaining: {remaining} apps")
        print(f"{'='*70}")
        
        batch_info = {
            'batch_size': current_batch_size,
            'success_rate': batch_sizer.recent_success_rates[-1] if batch_sizer.recent_success_rates else 0
        }
        
        generate_batch_instructions(batch, batch_info)
        
        # Generate the actual batch data for the agent
        print("\nBatch data for agent:")
        print("=" * 70)
        for app_name, url, status in batch:
            print(f"  - {app_name}: {url}")
        print("=" * 70)
        print(f"\n💡 After processing, record results:")
        print(f"   Success: X/{len(batch)} | Batch size will auto-adjust")
        print(f"   Estimated remaining batches: ~{int(estimated_batches)}")
        
        processed += len(batch)
        
        if processed < len(apps):
            print(f"\n⏸️  Process this batch, then continue...")
            try:
                input()
            except KeyboardInterrupt:
                print("\n\nStopped by user.")
                break

if __name__ == "__main__":
    main()










