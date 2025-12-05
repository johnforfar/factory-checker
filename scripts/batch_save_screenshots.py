#!/usr/bin/env python3
"""
Batch save screenshots from temp directory to app directories
"""
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")
TEMP_DIR = "/var/folders/bn/ml8l4wps6770plhr2r14g0dm0000gn/T/cursor/screenshots"

def save_screenshot(app_name, temp_filename):
    """Save screenshot from temp to app directory"""
    app_dir = os.path.join(APPS_DIR, app_name)
    temp_path = os.path.join(TEMP_DIR, temp_filename)
    dest_path = os.path.join(app_dir, "screenshot-1.png")
    
    if not os.path.exists(temp_path):
        return False
    
    os.makedirs(app_dir, exist_ok=True)
    try:
        subprocess.run(["cp", temp_path, dest_path], check=True)
        return True
    except:
        return False

if __name__ == "__main__":
    # Apps processed in this batch
    apps = [
        ("demof", "demof-screenshot.png"),
        ("derty", "derty-screenshot.png"),
        ("devil-app", "devil-app-screenshot.png"),
        ("dex-slippage-guard", "dex-slippage-guard-screenshot.png"),
        ("dexarbitrage", "dexarbitrage-screenshot.png"),
        ("dexvolemetracker", "dexvolemetracker-screenshot.png"),
        ("dexvolume", "dexvolume-screenshot.png"),
        ("dik", "dik-screenshot.png"),
        ("dm-app", "dm-app-screenshot.png"),
        ("document-assistant", "document-assistant-screenshot.png"),
        ("donnaapp", "donnaapp-screenshot.png"),
        ("dont-worry", "dont-worry-screenshot.png"),
        ("doodle-mint", "doodle-mint-screenshot.png"),
        ("dope", "dope-screenshot.png"),
        ("dragonbase", "dragonbase-screenshot.png"),
        ("dreaminterpreter", "dreaminterpreter-screenshot.png"),
        ("drip", "drip-screenshot.png"),
        ("dulal", "dulal-screenshot.png"),
        ("echo-app", "echo-app-screenshot.png"),
        ("ehte", "ehte-screenshot.png"),
        ("eligablity", "eligablity-screenshot.png"),
        ("elsa", "elsa-screenshot.png"),
        ("emojigame", "emojigame-screenshot.png"),
        ("emojimeaning", "emojimeaning-screenshot.png"),
        ("emojitranslator", "emojitranslator-screenshot.png"),
        ("endlessrunner", "endlessrunner-screenshot.png"),
        ("entry-exit-planne", "entry-exit-planne-screenshot.png"),
    ]
    
    saved = 0
    for app_name, filename in apps:
        if save_screenshot(app_name, filename):
            saved += 1
    
    print(f"Saved {saved} screenshots")












