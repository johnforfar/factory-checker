#!/usr/bin/env python3
"""
Analyze screenshot quality to assess visual polish and customization.
This checks if the app is a default template vs customized.
"""
import os
import json
from PIL import Image
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")

def analyze_screenshot(screenshot_path):
    """Analyze screenshot for quality indicators"""
    if not os.path.exists(screenshot_path):
        return {
            'has_screenshot': False,
            'is_default_template': None,
            'visual_quality': None,
            'has_custom_content': None
        }
    
    try:
        img = Image.open(screenshot_path)
        width, height = img.size
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get pixel data
        pixels = list(img.getdata())
        
        # Check for default template indicators
        # Default templates typically have:
        # 1. Mostly white/light backgrounds
        # 2. Simple text layouts
        # 3. Generic "Mini App Factory" branding
        
        # Analyze color distribution
        white_pixels = sum(1 for p in pixels if sum(p) > 700)  # Very light pixels
        total_pixels = len(pixels)
        white_ratio = white_pixels / total_pixels if total_pixels > 0 else 0
        
        # Check for color diversity (customized apps have more colors)
        unique_colors = len(set(pixels))
        color_diversity = unique_colors / total_pixels if total_pixels > 0 else 0
        
        # Estimate visual complexity
        # More complex = more likely customized
        is_likely_default = white_ratio > 0.8 and color_diversity < 0.01
        
        # Visual quality score (0-100)
        # Higher score = more customized/visually interesting
        visual_quality = 0
        
        if white_ratio < 0.7:  # Not mostly white
            visual_quality += 30
        if color_diversity > 0.01:  # Has color variety
            visual_quality += 30
        if unique_colors > 100:  # Many unique colors
            visual_quality += 20
        if width > 800 and height > 600:  # Good resolution
            visual_quality += 20
        
        return {
            'has_screenshot': True,
            'is_default_template': is_likely_default,
            'visual_quality': min(visual_quality, 100),
            'has_custom_content': not is_likely_default,
            'white_ratio': white_ratio,
            'color_diversity': color_diversity,
            'unique_colors': unique_colors,
            'dimensions': (width, height)
        }
    except Exception as e:
        return {
            'has_screenshot': True,
            'error': str(e),
            'is_default_template': None,
            'visual_quality': None
        }

def check_default_text_in_screenshot(screenshot_path):
    """Check if screenshot contains default template text"""
    # This would require OCR, but we can check file size/complexity as proxy
    # Smaller, simpler images = more likely default template
    try:
        size = os.path.getsize(screenshot_path)
        img = Image.open(screenshot_path)
        width, height = img.size
        
        # Very small or very simple images might be default templates
        is_simple = size < 50000 and width < 1000 and height < 1000
        
        return is_simple
    except:
        return None

def analyze_all_screenshots():
    """Analyze all screenshots and update state"""
    from datetime import datetime
    
    if not os.path.exists(STATE_FILE):
        print(f"State file not found: {STATE_FILE}")
        return
    
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
    
    analyzed = 0
    for app_name, app_data in state.items():
        app_path = os.path.join(APPS_DIR, app_name)
        if not os.path.exists(app_path):
            continue
        
        files = os.listdir(app_path)
        screenshots = [f for f in files if f.endswith('.png') and 'icon' not in f.lower() and 'logo' not in f.lower()]
        
        if screenshots:
            screenshot_path = os.path.join(app_path, screenshots[0])
            analysis = analyze_screenshot(screenshot_path)
            
            # Store analysis in state
            app_data['screenshot_analysis'] = {
                'visual_quality': analysis.get('visual_quality'),
                'is_default_template': analysis.get('is_default_template'),
                'has_custom_content': analysis.get('has_custom_content'),
                'white_ratio': analysis.get('white_ratio'),
                'color_diversity': analysis.get('color_diversity'),
                'unique_colors': analysis.get('unique_colors'),
                'analyzed_at': datetime.now().isoformat()
            }
            
            analyzed += 1
    
    # Save updated state
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    
    print(f"Analyzed {analyzed} screenshots")
    return analyzed

if __name__ == "__main__":
    from datetime import datetime
    analyze_all_screenshots()

