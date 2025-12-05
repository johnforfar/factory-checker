#!/usr/bin/env python3
"""
Compress screenshots to reduce file size while maintaining reasonable quality.
Uses PIL/Pillow to optimize PNG images.
"""
import os
from PIL import Image
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

def compress_image(input_path, output_path=None, quality=85, max_size=(1920, 1080)):
    """
    Compress an image file.
    
    Args:
        input_path: Path to input image
        output_path: Path to save compressed image (if None, overwrites input)
        quality: JPEG quality (1-100) or PNG optimization level
        max_size: Maximum dimensions (width, height)
    """
    if output_path is None:
        output_path = input_path
    
    try:
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if needed (for JPEG)
            if img.mode == 'RGBA':
                # Create white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])  # Use alpha channel as mask
                img = rgb_img
            
            # Resize if too large
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized
            if input_path.lower().endswith('.png'):
                # PNG: Use optimize flag and reduce colors if possible
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
            else:
                # JPEG or other formats
                img.save(output_path, quality=quality, optimize=True)
            
        return True
    except Exception as e:
        print(f"Error compressing {input_path}: {e}")
        return False

def compress_all_screenshots():
    """Compress all screenshots in the apps directory"""
    total_files = 0
    compressed_files = 0
    total_saved = 0
    
    if not os.path.exists(APPS_DIR):
        print(f"Apps directory not found: {APPS_DIR}")
        return
    
    for app_name in os.listdir(APPS_DIR):
        app_path = os.path.join(APPS_DIR, app_name)
        if not os.path.isdir(app_path):
            continue
        
        for filename in os.listdir(app_path):
            # Only process screenshot files (not icons/logos)
            if filename.startswith('screenshot') and filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(app_path, filename)
                
                # Get original size
                original_size = os.path.getsize(file_path)
                
                # Compress
                if compress_image(file_path):
                    compressed_size = os.path.getsize(file_path)
                    saved = original_size - compressed_size
                    total_saved += saved
                    compressed_files += 1
                    
                    if saved > 0:
                        print(f"✓ {app_name}/{filename}: {original_size:,} → {compressed_size:,} bytes ({saved:,} saved, {saved/original_size*100:.1f}%)")
                    else:
                        print(f"  {app_name}/{filename}: Already optimized")
                else:
                    print(f"✗ Failed to compress {app_name}/{filename}")
                
                total_files += 1
    
    print(f"\n{'='*60}")
    print(f"Compression Summary:")
    print(f"  Total files processed: {total_files}")
    print(f"  Successfully compressed: {compressed_files}")
    print(f"  Total space saved: {total_saved:,} bytes ({total_saved/1024/1024:.2f} MB)")
    print(f"{'='*60}")

if __name__ == "__main__":
    compress_all_screenshots()












