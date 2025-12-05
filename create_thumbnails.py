#!/usr/bin/env python3
"""
Create thumbnail versions of screenshots for faster loading in list views.
Thumbnails are smaller files that load faster, while full-size images load only in modal.
"""
import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")
THUMBNAIL_SIZE = (300, 200)  # Max width 300px, height scales proportionally

def create_thumbnail(input_path, output_path, max_size=THUMBNAIL_SIZE):
    """
    Create a thumbnail version of an image.
    
    Args:
        input_path: Path to original screenshot
        output_path: Path to save thumbnail
        max_size: Maximum dimensions (width, height)
    """
    try:
        # Check if file exists and has content
        if not os.path.exists(input_path):
            return False, 0, 0
        
        file_size = os.path.getsize(input_path)
        if file_size == 0:
            # Empty file - remove it to prevent 404s
            try:
                os.remove(input_path)
                print(f"  Removed empty file: {input_path}")
            except:
                pass
            return False, 0, 0
        
        # Validate image before processing
        with Image.open(input_path) as img:
            # Verify image is valid
            img.verify()
        
        # Reopen after verify (verify closes the file)
        with Image.open(input_path) as img:
            # Check dimensions
            width, height = img.size
            if width == 0 or height == 0 or width < 10 or height < 10:
                # Invalid dimensions - remove corrupted file
                try:
                    os.remove(input_path)
                    print(f"  Removed invalid image (bad dimensions): {input_path}")
                except:
                    pass
                return False, 0, 0
            
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            
            # Create thumbnail maintaining aspect ratio
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized thumbnail
            img.save(output_path, 'PNG', optimize=True, compress_level=9)
            
            return True, file_size, os.path.getsize(output_path)
    except Exception as e:
        # Image is corrupted - try to remove it
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
                print(f"  Removed corrupted file: {input_path} ({e})")
        except:
            pass
        return False, 0, 0

def create_all_thumbnails():
    """Create thumbnails for all screenshots"""
    total_files = 0
    created_files = 0
    total_original_size = 0
    total_thumbnail_size = 0
    
    if not os.path.exists(APPS_DIR):
        print(f"Apps directory not found: {APPS_DIR}")
        return
    
    print(f"Creating thumbnails ({THUMBNAIL_SIZE[0]}x{THUMBNAIL_SIZE[1]} max)...\n")
    
    for app_name in sorted(os.listdir(APPS_DIR)):
        app_path = os.path.join(APPS_DIR, app_name)
        if not os.path.isdir(app_path):
            continue
        
        for filename in os.listdir(app_path):
            # Only process screenshot files (exclude thumbnails, icons, logos)
            # Process any PNG/JPG that's not a thumbnail, icon, or logo
            if (filename.lower().endswith(('.png', '.jpg', '.jpeg')) and 
                '-thumb' not in filename.lower() and 
                'icon' not in filename.lower() and 
                'logo' not in filename.lower()):
                file_path = os.path.join(app_path, filename)
                
                # Create thumbnail filename (e.g., screenshot-1.png -> screenshot-1-thumb.png)
                # Remove any existing -thumb suffixes first
                import re
                clean_name = re.sub(r'-thumb+', '', filename)
                name, ext = os.path.splitext(clean_name)
                thumbnail_filename = f"{name}-thumb{ext}"
                thumbnail_path = os.path.join(app_path, thumbnail_filename)
                
                # Skip if thumbnail already exists and is newer
                if os.path.exists(thumbnail_path):
                    if os.path.getmtime(thumbnail_path) >= os.path.getmtime(file_path):
                        continue
                
                # Create thumbnail
                success, orig_size, thumb_size = create_thumbnail(file_path, thumbnail_path)
                
                if success:
                    total_original_size += orig_size
                    total_thumbnail_size += thumb_size
                    created_files += 1
                    saved = orig_size - thumb_size
                    savings_pct = (saved / orig_size * 100) if orig_size > 0 else 0
                    
                    if saved > 0:
                        print(f"✓ {app_name}/{filename}: {orig_size:,} → {thumb_size:,} bytes ({saved:,} saved, {savings_pct:.1f}%)")
                    else:
                        print(f"  {app_name}/{filename}: Thumbnail created ({thumb_size:,} bytes)")
                # Note: Failed thumbnails are now handled inside create_thumbnail (file removal)
                # We don't print here to avoid duplicate messages
                
                total_files += 1
    
    print(f"\n{'='*60}")
    print(f"Thumbnail Creation Summary:")
    print(f"  Total files processed: {total_files}")
    print(f"  Thumbnails created/updated: {created_files}")
    print(f"  Total original size: {total_original_size:,} bytes ({total_original_size/1024/1024:.2f} MB)")
    print(f"  Total thumbnail size: {total_thumbnail_size:,} bytes ({total_thumbnail_size/1024/1024:.2f} MB)")
    print(f"  Total space saved (for thumbnails): {total_original_size - total_thumbnail_size:,} bytes ({(total_original_size - total_thumbnail_size)/1024/1024:.2f} MB)")
    print(f"  Average thumbnail size: {total_thumbnail_size/created_files if created_files > 0 else 0:,.0f} bytes")
    print(f"{'='*60}")

if __name__ == "__main__":
    create_all_thumbnails()

