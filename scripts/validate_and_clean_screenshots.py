#!/usr/bin/env python3
"""
Robust screenshot validation and cleanup script.
This script:
1. Validates all screenshot files exist and are valid images
2. Removes empty, corrupted, or invalid files
3. Ensures thumbnails exist for all valid screenshots
4. Reports any issues found
"""
import os
import sys
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")
THUMBNAIL_SIZE = (300, 200)

def is_valid_image(file_path):
    """Check if a file is a valid, non-empty image"""
    try:
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return False, "File is empty (0 bytes)"
        
        # Try to open and verify the image
        with Image.open(file_path) as img:
            img.verify()
        
        # Reopen to check dimensions (verify closes the file)
        with Image.open(file_path) as img:
            width, height = img.size
            if width == 0 or height == 0:
                return False, f"Invalid dimensions ({width}x{height})"
            
            # Check minimum reasonable size (at least 10x10 pixels)
            if width < 10 or height < 10:
                return False, f"Too small ({width}x{height})"
        
        return True, None
    except Exception as e:
        return False, f"Invalid image: {str(e)}"

def create_thumbnail(input_path, output_path, max_size=THUMBNAIL_SIZE):
    """Create a thumbnail version of an image"""
    try:
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            
            # Create thumbnail maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized thumbnail
            img.save(output_path, 'PNG', optimize=True, compress_level=9)
            
            return True
    except Exception as e:
        print(f"    Error creating thumbnail: {e}")
        return False

def validate_and_clean_app(app_name, app_path, dry_run=False):
    """Validate and clean screenshots for a single app"""
    issues = []
    fixed = []
    removed = []
    
    if not os.path.isdir(app_path):
        return issues, fixed, removed
    
    files = os.listdir(app_path)
    
    # Process all image files
    for filename in files:
        file_path = os.path.join(app_path, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
        
        # Only process image files
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        
        # Skip icons and logos (they're handled separately)
        if 'icon' in filename.lower() or 'logo' in filename.lower():
            continue
        
        # Check if it's a thumbnail
        is_thumbnail = '-thumb' in filename.lower()
        
        if is_thumbnail:
            # For thumbnails, check if the original exists
            import re
            clean_name = re.sub(r'-thumb+', '', filename)
            original_path = os.path.join(app_path, clean_name)
            
            if not os.path.exists(original_path):
                # Orphaned thumbnail - remove it
                if not dry_run:
                    os.remove(file_path)
                removed.append(f"{app_name}/{filename} (orphaned thumbnail)")
                continue
            
            # Validate thumbnail
            is_valid, error = is_valid_image(file_path)
            if not is_valid:
                if not dry_run:
                    os.remove(file_path)
                    # Try to recreate from original
                    if create_thumbnail(original_path, file_path):
                        fixed.append(f"{app_name}/{filename} (recreated)")
                    else:
                        removed.append(f"{app_name}/{filename} ({error})")
                else:
                    issues.append(f"{app_name}/{filename}: {error}")
        else:
            # This is a screenshot (not a thumbnail)
            is_valid, error = is_valid_image(file_path)
            
            if not is_valid:
                # Invalid screenshot - remove it and its thumbnail if it exists
                import re
                clean_name = re.sub(r'-thumb+', '', filename)
                name, ext = os.path.splitext(clean_name)
                thumbnail_filename = f"{name}-thumb{ext}"
                thumbnail_path = os.path.join(app_path, thumbnail_filename)
                
                if not dry_run:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    if os.path.exists(thumbnail_path):
                        os.remove(thumbnail_path)
                    removed.append(f"{app_name}/{filename} ({error})")
                else:
                    issues.append(f"{app_name}/{filename}: {error}")
            else:
                # Valid screenshot - ensure thumbnail exists
                import re
                clean_name = re.sub(r'-thumb+', '', filename)
                name, ext = os.path.splitext(clean_name)
                thumbnail_filename = f"{name}-thumb{ext}"
                thumbnail_path = os.path.join(app_path, thumbnail_filename)
                
                # Check if thumbnail needs to be created/updated
                needs_thumbnail = True
                if os.path.exists(thumbnail_path):
                    # Check if thumbnail is valid and up-to-date
                    thumb_valid, thumb_error = is_valid_image(thumbnail_path)
                    if thumb_valid:
                        # Check if thumbnail is newer than original
                        if os.path.getmtime(thumbnail_path) >= os.path.getmtime(file_path):
                            needs_thumbnail = False
                
                if needs_thumbnail:
                    if not dry_run:
                        if create_thumbnail(file_path, thumbnail_path):
                            fixed.append(f"{app_name}/{thumbnail_filename} (created)")
                        else:
                            issues.append(f"{app_name}/{filename}: Failed to create thumbnail")
                    else:
                        issues.append(f"{app_name}/{filename}: Missing or outdated thumbnail")
    
    return issues, fixed, removed

def validate_and_clean_all(dry_run=False):
    """Validate and clean all screenshots"""
    if not os.path.exists(APPS_DIR):
        print(f"Apps directory not found: {APPS_DIR}")
        return
    
    print(f"{'DRY RUN: ' if dry_run else ''}Validating and cleaning screenshots...\n")
    
    all_issues = []
    all_fixed = []
    all_removed = []
    
    for app_name in sorted(os.listdir(APPS_DIR)):
        app_path = os.path.join(APPS_DIR, app_name)
        issues, fixed, removed = validate_and_clean_app(app_name, app_path, dry_run)
        
        all_issues.extend(issues)
        all_fixed.extend(fixed)
        all_removed.extend(removed)
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*70}")
    print(f"  Issues found: {len(all_issues)}")
    print(f"  Files fixed: {len(all_fixed)}")
    print(f"  Files removed: {len(all_removed)}")
    print(f"{'='*70}\n")
    
    if all_removed:
        print(f"Removed files ({len(all_removed)}):")
        for item in all_removed[:20]:  # Show first 20
            print(f"  ✗ {item}")
        if len(all_removed) > 20:
            print(f"  ... and {len(all_removed) - 20} more")
        print()
    
    if all_fixed:
        print(f"Fixed files ({len(all_fixed)}):")
        for item in all_fixed[:20]:  # Show first 20
            print(f"  ✓ {item}")
        if len(all_fixed) > 20:
            print(f"  ... and {len(all_fixed) - 20} more")
        print()
    
    if all_issues:
        print(f"Issues found ({len(all_issues)}):")
        for item in all_issues[:20]:  # Show first 20
            print(f"  ⚠ {item}")
        if len(all_issues) > 20:
            print(f"  ... and {len(all_issues) - 20} more")
        print()
    
    if dry_run and (all_issues or all_removed):
        print("Run without --dry-run to fix these issues.")
    elif not dry_run:
        print("✓ Validation and cleanup complete!")

if __name__ == "__main__":
    dry_run = '--dry-run' in sys.argv
    validate_and_clean_all(dry_run=dry_run)












