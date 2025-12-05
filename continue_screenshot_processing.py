#!/usr/bin/env python3
"""
Continue processing screenshots in batches with adaptive batch sizing.
Implements TCP-like windowing: doubles batch size when stable, reduces when unstable.
"""
import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")
BATCH_STATE_FILE = os.path.join(BASE_DIR, ".batch_state.json")

# Adaptive windowing configuration
MIN_BATCH_SIZE = 2
MAX_BATCH_SIZE = 64
INITIAL_BATCH_SIZE = 6
SUCCESS_THRESHOLD = 0.90  # 90% success rate to increase batch size
STABILITY_WINDOW = 3  # Number of consecutive successful batches before increasing
REDUCE_THRESHOLD = 0.70  # Below 70% success rate, reduce batch size

def load_state():
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def get_stats():
    """Get current statistics"""
    state = load_state()
    total = len(state)
    complete = 0
    incomplete = 0
    needing_screenshots = 0
    
    for name, data in state.items():
        app_path = os.path.join(APPS_DIR, name)
        
        has_github = data.get('last_updated') and data.get('last_updated') != 'Never' and data.get('last_updated') != 'Unknown'
        has_icon = False
        has_screenshot = False
        
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            has_icon = any('icon' in f.lower() or 'logo' in f.lower() for f in files if f.endswith('.png'))
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
            has_screenshot = len(screenshots) > 0
        
        if has_github and has_icon and has_screenshot:
            complete += 1
        else:
            incomplete += 1
            if not has_screenshot:
                needing_screenshots += 1
    
    return {
        'total': total,
        'complete': complete,
        'incomplete': incomplete,
        'needing_screenshots': needing_screenshots
    }

def load_batch_state():
    """Load batch state (for adaptive sizing)"""
    if os.path.exists(BATCH_STATE_FILE):
        with open(BATCH_STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'current_batch_size': INITIAL_BATCH_SIZE,
        'recent_success_rates': [],
        'consecutive_successful_batches': 0
    }

def save_batch_state(batch_state):
    """Save batch state"""
    with open(BATCH_STATE_FILE, 'w') as f:
        json.dump(batch_state, f, indent=2)

def record_batch_result(success_count, total_count):
    """Record batch result and adjust batch size"""
    batch_state = load_batch_state()
    
    if total_count == 0:
        return batch_state['current_batch_size']
    
    success_rate = success_count / total_count
    batch_state['recent_success_rates'].append(success_rate)
    
    # Keep only last STABILITY_WINDOW batches
    if len(batch_state['recent_success_rates']) > STABILITY_WINDOW:
        batch_state['recent_success_rates'].pop(0)
    
    old_size = batch_state['current_batch_size']
    
    # Adjust batch size based on performance
    if success_rate >= SUCCESS_THRESHOLD:
        batch_state['consecutive_successful_batches'] += 1
        
        # If we've had STABILITY_WINDOW consecutive successful batches, increase size
        if batch_state['consecutive_successful_batches'] >= STABILITY_WINDOW:
            if batch_state['current_batch_size'] < MAX_BATCH_SIZE:
                batch_state['current_batch_size'] = min(batch_state['current_batch_size'] * 2, MAX_BATCH_SIZE)
                batch_state['consecutive_successful_batches'] = 0
                print(f"📈 Batch size increased: {old_size} → {batch_state['current_batch_size']} (success rate: {success_rate:.1%})")
    else:
        batch_state['consecutive_successful_batches'] = 0
    
    # Reduce batch size if success rate drops too low
    if success_rate < REDUCE_THRESHOLD:
        if batch_state['current_batch_size'] > MIN_BATCH_SIZE:
            batch_state['current_batch_size'] = max(batch_state['current_batch_size'] // 2, MIN_BATCH_SIZE)
            print(f"📉 Batch size reduced: {old_size} → {batch_state['current_batch_size']} (success rate: {success_rate:.1%})")
            batch_state['recent_success_rates'] = []  # Reset history after reduction
    
    save_batch_state(batch_state)
    return batch_state['current_batch_size']

def auto_detect_last_batch_result():
    """Auto-detect results from the last processed batch by checking saved screenshots"""
    batch_state = load_batch_state()
    last_batch_size = batch_state.get('last_batch_size', 0)
    last_batch_apps = batch_state.get('last_batch_apps', [])
    
    if not last_batch_apps or last_batch_size == 0:
        return None
    
    success_count = 0
    for app_name in last_batch_apps:
        app_path = os.path.join(APPS_DIR, app_name)
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            screenshots = [f for f in files if f.endswith('.png') and 
                          'icon' not in f.lower() and 'logo' not in f.lower() and 
                          'thumb' not in f.lower()]
            if len(screenshots) > 0:
                success_count += 1
    
    return success_count, len(last_batch_apps)

def get_next_batch(size=None):
    """Get next batch of apps needing screenshots with adaptive sizing"""
    # Auto-detect and record results from last batch
    last_result = auto_detect_last_batch_result()
    if last_result:
        success, total = last_result
        if success < total:  # Only adjust if not all succeeded (some might have been skipped)
            record_batch_result(success, total)
    
    # Use adaptive batch size if not specified
    if size is None:
        batch_state = load_batch_state()
        size = batch_state['current_batch_size']
    
    state = load_state()
    needs_screenshots = []
    
    for name, data in state.items():
        app_path = os.path.join(APPS_DIR, name)
        screenshots = []
        
        if os.path.exists(app_path):
            files = os.listdir(app_path)
            screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower() and 'thumb' not in f.lower()]
        
        if len(screenshots) == 0:
            url = f"https://{name}.miniapp-factory.marketplace.openxai.network/"
            status = data.get('status', 'Pending')
            needs_screenshots.append((name, url, status))
            if len(needs_screenshots) >= size:
                break
    
    # Save current batch for auto-detection
    batch_state = load_batch_state()
    batch_state['last_batch_size'] = len(needs_screenshots)
    batch_state['last_batch_apps'] = [name for name, _, _ in needs_screenshots]
    save_batch_state(batch_state)
    
    return needs_screenshots

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Continue screenshot processing with adaptive batch sizing')
    parser.add_argument('--batch-size', type=int, default=None, help='Override batch size (uses adaptive by default)')
    parser.add_argument('--stats-only', action='store_true', help='Show stats only')
    parser.add_argument('--record-result', type=str, help='Record batch result: "success/total" (e.g., "5/6")')
    parser.add_argument('--reset', action='store_true', help='Reset adaptive batch state')
    
    args = parser.parse_args()
    
    # Handle reset
    if args.reset:
        if os.path.exists(BATCH_STATE_FILE):
            os.remove(BATCH_STATE_FILE)
            print("✅ Batch state reset")
        return
    
    # Handle recording result
    if args.record_result:
        try:
            parts = args.record_result.split('/')
            success = int(parts[0])
            total = int(parts[1])
            new_size = record_batch_result(success, total)
            print(f"✅ Recorded: {success}/{total} ({success/total:.1%}) | New batch size: {new_size}")
        except Exception as e:
            print(f"❌ Error recording result: {e}")
        return
    
    stats = get_stats()
    batch_state = load_batch_state()
    
    print(f"\n{'='*70}")
    print(f"SCREENSHOT PROCESSING STATUS (Adaptive Batch Sizing)")
    print(f"{'='*70}")
    print(f"Total apps: {stats['total']}")
    print(f"Complete: {stats['complete']} ({stats['complete']*100/stats['total']:.1f}%)")
    print(f"Incomplete: {stats['incomplete']} ({stats['incomplete']*100/stats['total']:.1f}%)")
    print(f"Needing screenshots: {stats['needing_screenshots']}")
    print(f"\nCurrent batch size: {batch_state['current_batch_size']} (range: {MIN_BATCH_SIZE}-{MAX_BATCH_SIZE})")
    if batch_state['recent_success_rates']:
        avg_rate = sum(batch_state['recent_success_rates']) / len(batch_state['recent_success_rates'])
        print(f"Recent success rate: {avg_rate:.1%} (last {len(batch_state['recent_success_rates'])} batches)")
    print(f"{'='*70}\n")
    
    if args.stats_only:
        return
    
    batch = get_next_batch(args.batch_size)
    
    if len(batch) == 0:
        print("✅ All apps have screenshots!")
        return
    
    print(f"Next batch ({len(batch)} apps):\n")
    for i, (name, url, status) in enumerate(batch, 1):
        print(f"{i:3d}. [{status:8s}] {name:35s} -> {url}")
    
    print(f"\n{'='*70}")
    print("To process this batch:")
    print("1. Take screenshots using browser automation")
    print("2. Save to: app-review/public/apps/{app_name}/screenshot-1.png")
    print("3. Run: python3 process_batch_screenshots.py --update-only")
    print("4. Batch size will auto-adjust based on success rate")
    print(f"{'='*70}\n")
    
    # Auto-detect results from previous batch if available
    # This allows automatic adjustment without manual recording
    print("💡 Tip: After processing, batch size will automatically adjust")
    print("   based on success rate (doubles if >90%, halves if <70%)\n")

if __name__ == "__main__":
    main()

