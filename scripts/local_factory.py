import os
import shutil
import subprocess
import sys
import time
import json
import urllib.request
import urllib.error

# Configuration
PROJECT_NAME = "space-invaders"
TEMPLATE_DIR = os.path.abspath("template")
OUTPUT_DIR = os.path.abspath("out")
TARGET_DIR = os.path.join(OUTPUT_DIR, PROJECT_NAME)
MODEL = "gpt-oss:20b" # The raw model name in Ollama
AIDER_MODEL = f"ollama_chat/{MODEL}" # The model name passed to Aider

# The Ultimate Prompt
INSTRUCTIONS = r"""
Code the following app
```
A Space Invaders game using Three.js.

**1. Dependency Setup**
- Add "three": "^0.170.0" to dependencies in package.json.
- Add "@types/three": "^0.170.0" to devDependencies in package.json to prevent build errors.

**2. Component Implementation**
Create components/space-invaders.tsx with "use client;" at the top.
- Use import * as THREE from "three";
- Implement a SpaceInvaders component that returns a <div ref={mountRef} className="w-full h-screen relative" />.
- Inside useEffect, initialize the Three.js WebGLRenderer, Scene, and PerspectiveCamera.
- CRITICAL: Handle React Strict Mode by checking if the renderer already exists or strictly cleaning up in the return function.
- Cleanup: In the useEffect return function, remove the renderer.domElement from the mount point, dispose of geometries/materials, and cancel the animation frame request.

**3. Game Logic & State**
- Player: A green box mesh at the bottom (y = -4). Moves left/right with Arrow keys or Touch (calculate touch delta).
- Invaders: A grid (5 rows x 10 columns) of red box meshes starting at y = 3. They move horizontally, hitting the edge (x = +/- 6) shifts them down.
- Projectiles: 
  - Player shoots yellow small spheres (Spacebar or UI Button).
  - Invaders shoot white small spheres randomly.
- Collision:
  - Use THREE.Box3 to detect overlaps between projectiles and meshes.
  - Player hit = -1 life.
  - Invader hit = +10 score & remove invader.
- Game Loop: Use requestAnimationFrame. Update positions, check collisions, render scene.

**4. UI & Overlays**
- Use HTML/Tailwind overlays (absolute positioning over the canvas) for:
  - Score (Top Left).
  - Lives (Top Right).
  - Game Over Screen: Centered div with final score and a <Share text={...} /> button (import from @/components/share). Show this when lives == 0 or all invaders destroyed.
  - Mobile Controls: A visible "FIRE" button (using @/components/ui/button) in the bottom right corner, only visible on touch devices (or always visible).

**5. Assets**
- Metadata: Update lib/metadata.ts title to "Space Invaders 3D".
- Images: Create the following files:
  - public/logo.png.todo:
    512x512
    Pixel art icon of a green space invader alien on a black background, arcade style.
  - public/player.png.todo:
    512x512
    Top-down view of a futuristic spaceship, triangular, neon green details, black background.

**6. Integration**
- In app/page.tsx, remove the default content.
- Import SpaceInvaders from @/components/space-invaders.
- Render <SpaceInvaders /> as the main element.
- Keep export { generateMetadata } from "@/lib/metadata";.

Ensure all code is valid TypeScript. Define interfaces for Projectile and Enemy objects. Do not use any.
```
Generate an app logo and update the app metadata title and description.
"""

def run_command(cmd, cwd=None, env=None):
    print(f"Running: {' '.join(cmd)}")
    # Use Popen to stream output
    process = subprocess.Popen(
        cmd, 
        cwd=cwd, 
        env=env, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, # Redirect stderr to stdout
        text=True,
        bufsize=1
    )
    
    for line in process.stdout:
        print(line, end='')
        sys.stdout.flush() # Ensure immediate output
    
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)

def check_model_availability(model_name):
    print(f"Checking if model '{model_name}' is available in Ollama...")
    url = "http://127.0.0.1:11434/api/tags"
    while True:
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    models = [m['name'] for m in data.get('models', [])]
                    if any(model_name in m for m in models):
                        print(f"Model '{model_name}' found!")
                        return True
            print(f"Model '{model_name}' not found yet. Retrying in 5 seconds...")
        except Exception as e:
             print(f"Error connecting to Ollama: {e}. Retrying in 5 seconds...")
        
        time.sleep(5)

def main():
    # 0. Wait for Model
    check_model_availability(MODEL)

    # 1. Prepare Directories
    if os.path.exists(TARGET_DIR):
        print(f"Cleaning existing directory: {TARGET_DIR}")
        shutil.rmtree(TARGET_DIR)
    
    print(f"Cloning template to: {TARGET_DIR}")
    # Clone with full logging
    subprocess.run(["git", "clone", TEMPLATE_DIR, TARGET_DIR], check=True)

    # 2. Setup Environment for Aider
    mini_app_dir = os.path.join(TARGET_DIR, "mini-app")
    
    print("Installing dependencies...")
    run_command(["npm", "install"], cwd=mini_app_dir)

    # 3. Run Aider
    print(f"Starting Aider with model {AIDER_MODEL}...")
    
    env = os.environ.copy()
    env["OLLAMA_API_BASE"] = "http://127.0.0.1:11434"

    aider_cmd = [
        "aider",
        "--model", AIDER_MODEL,
        "--no-auto-commits",
        "--yes-always",
        "--message", INSTRUCTIONS,
        "--read", os.path.join(TARGET_DIR, "documentation", "index.md"),
        "--edit-format", "diff",
        "--architect",
    ]

    try:
        run_command(aider_cmd, cwd=mini_app_dir, env=env)
        print("\nSUCCESS! Aider has finished coding.")
        print(f"Your new app is ready in: {mini_app_dir}")
        print(f"To run it:\n  cd {mini_app_dir}\n  npm run dev")
    except subprocess.CalledProcessError as e:
        print(f"Aider failed with error: {e}")

if __name__ == "__main__":
    main()
