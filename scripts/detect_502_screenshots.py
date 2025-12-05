#!/usr/bin/env python3
"""
Detect screenshots that show 502 Bad Gateway errors.
These screenshots reflect server issues, not app quality, so they should be removed or retried.
"""
import os
from PIL import Image
import pytesseract

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

def is_502_error_screenshot(image_path):
    """
    Check if a screenshot shows a 502 Bad Gateway error.
    Uses OCR to detect the error text and checks for characteristic black background.
    """
    try:
        with Image.open(image_path) as img:
            # Check image dimensions
            width, height = img.size
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Sample pixels to check if it's mostly black (502 error pages are black)
            # Sample a grid of pixels
            sample_size = 20
            black_pixels = 0
            total_samples = 0
            
            for x in range(0, width, width // sample_size):
                for y in range(0, height, height // sample_size):
                    if x < width and y < height:
                        r, g, b = img.getpixel((x, y))
                        # Check if pixel is very dark (close to black)
                        if r < 50 and g < 50 and b < 50:
                            black_pixels += 1
                        total_samples += 1
            
            black_ratio = black_pixels / total_samples if total_samples > 0 else 0
            
            # If image is mostly black, it might be a 502 error
            if black_ratio > 0.8:
                # Try OCR to confirm it's a 502 error
                try:
                    # Use OCR to extract text
                    text = pytesseract.image_to_string(img).lower()
                    if '502' in text and ('bad gateway' in text or 'gateway' in text):
                        return True, "502 Bad Gateway detected via OCR"
                    if 'nginx' in text and black_ratio > 0.9:
                        return True, "Nginx error page detected (likely 502)"
                except Exception as e:
                    # If OCR fails but image is mostly black, it's suspicious
                    if black_ratio > 0.95:
                        return True, f"Mostly black image (likely error page, OCR failed: {e})"
            
            return False, None
            
    except Exception as e:
        return False, f"Error analyzing image: {e}"

def find_502_screenshots():
    """Find all screenshots that show 502 errors"""
    error_screenshots = []
    
    if not os.path.exists(APPS_DIR):
        print(f"Apps directory not found: {APPS_DIR}")
        return error_screenshots
    
    print("Scanning screenshots for 502 Bad Gateway errors...\n")
    
    for app_name in sorted(os.listdir(APPS_DIR)):
        app_path = os.path.join(APPS_DIR, app_name)
        if not os.path.isdir(app_path):
            continue
        
        for filename in os.listdir(app_path):
            # Only check screenshot files (not thumbnails, icons, logos)
            if (filename.lower().endswith(('.png', '.jpg', '.jpeg')) and 
                '-thumb' not in filename.lower() and 
                'icon' not in filename.lower() and 
                'logo' not in filename.lower()):
                
                file_path = os.path.join(app_path, filename)
                
                # Check file size (empty files are not errors)
                if os.path.getsize(file_path) == 0:
                    continue
                
                is_error, reason = is_502_error_screenshot(file_path)
                
                if is_error:
                    error_screenshots.append({
                        'app': app_name,
                        'file': filename,
                        'path': file_path,
                        'reason': reason
                    })
                    print(f"✗ {app_name}/{filename}: {reason}")
    
    return error_screenshots

def remove_502_screenshots(dry_run=True):
    """Remove screenshots showing 502 errors"""
    error_screenshots = find_502_screenshots()
    
    print(f"\n{'='*70}")
    print(f"502 ERROR SCREENSHOT DETECTION")
    print(f"{'='*70}")
    print(f"Found {len(error_screenshots)} screenshots showing 502 errors")
    print(f"{'='*70}\n")
    
    if len(error_screenshots) == 0:
        print("✅ No 502 error screenshots found!")
        return
    
    if dry_run:
        print("DRY RUN - Would remove the following screenshots:\n")
        for item in error_screenshots:
            print(f"  {item['app']}/{item['file']}: {item['reason']}")
        print("\nRun without --dry-run to remove these files.")
    else:
        removed_count = 0
        for item in error_screenshots:
            try:
                os.remove(item['path'])
                # Also remove thumbnail if it exists
                thumb_path = item['path'].replace('.png', '-thumb.png').replace('.jpg', '-thumb.jpg').replace('.jpeg', '-thumb.jpeg')
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
                removed_count += 1
                print(f"✓ Removed {item['app']}/{item['file']}")
            except Exception as e:
                print(f"✗ Failed to remove {item['app']}/{item['file']}: {e}")
        
        print(f"\n✓ Removed {removed_count} error screenshots")

if __name__ == "__main__":
    import sys
    
    dry_run = '--dry-run' not in sys.argv or '--remove' not in sys.argv
    
    if '--remove' in sys.argv:
        remove_502_screenshots(dry_run=False)
    else:
        remove_502_screenshots(dry_run=True)












