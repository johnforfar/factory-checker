import json
import os
import subprocess
import time
import random
import concurrent.futures
from bs4 import BeautifulSoup
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")

# User agents
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def extract_all_prompts_from_history(content):
    """Extract all prompts from aider chat history (multiple sessions)."""
    if not content:
        return []
    
    prompts = []
    
    # Split by session markers
    sessions = re.split(r'# aider chat started at', content)
    
    for session in sessions:
        if not session.strip():
            continue
            
        # Pattern 1: Look for --message followed by a code block
        # Format: --message [text]\n```\n[prompt content]\n```
        pattern1 = re.search(r'--message\s+([^\n]+)\n```\n(.*?)```', session, re.DOTALL)
        if pattern1:
            message_type = pattern1.group(1).strip()
            prompt_text = pattern1.group(2).strip()
            
            # Skip if it's just "Code the following app" without actual prompt
            if prompt_text and len(prompt_text) > 20:
                prompts.append({
                    'type': message_type,
                    'text': prompt_text
                })
                continue
        
        # Pattern 2: Look for --message flag with single line (no code block)
        pattern2 = re.search(r'--message\s+([^\n]+)', session)
        if pattern2:
            prompt_text = pattern2.group(1).strip()
            # Remove trailing backslashes or quotes
            prompt_text = prompt_text.rstrip('\\').strip('"\'')
            if prompt_text and prompt_text != "Code the following app" and len(prompt_text) > 20:
                prompts.append({
                    'type': 'Direct message',
                    'text': prompt_text
                })
    
    return prompts

def extract_prompt_from_history(content):
    """Extract the initial prompt from aider chat history (backward compatibility)."""
    prompts = extract_all_prompts_from_history(content)
    if prompts:
        return prompts[0]['text']
    return None

def fetch_prompt_history(app_name):
    # Random delay
    time.sleep(random.uniform(1.0, 2.5))
    
    url = f"https://raw.githubusercontent.com/miniapp-factory/{app_name}/main/.aider.chat.history.md"
    ua = random.choice(USER_AGENTS)
    
    try:
        cmd = ["curl", "-s", "-H", f"User-Agent: {ua}", "--max-time", "10", url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return app_name, None, "Error"
            
        content = result.stdout
        
        if not content or "404" in content or "Not Found" in content:
            return app_name, None, "Not Found"
        
        prompts = extract_all_prompts_from_history(content)
        
        if prompts:
            # Store as array of prompts
            return app_name, prompts, "Success"
        else:
            return app_name, None, "No Prompt Found"
            
    except Exception as e:
        return app_name, None, f"Exception: {e}"

def main():
    with open(STATE_FILE, 'r') as f:
        state = json.load(f)
        
    # Process all apps, prioritizing Active ones
    apps_to_check = list(state.keys())
    
    print(f"Fetching prompt history for {len(apps_to_check)} apps...")
    
    count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_app = {executor.submit(fetch_prompt_history, app): app for app in apps_to_check}
        
        for future in concurrent.futures.as_completed(future_to_app):
            app_name = future_to_app[future]
            try:
                name, prompts, status = future.result()
                if status == "Success" and prompts:
                    state[name]['prompts'] = prompts  # Store as array
                    # Also keep single prompt for backward compatibility
                    state[name]['prompt'] = prompts[0]['text'] if prompts else None
                    count += 1
                    print(f"[{count}] {name}: Found {len(prompts)} prompt(s)")
                elif status == "Not Found":
                    # Maybe try alternative path?
                    pass
                    
                if count % 10 == 0:
                    with open(STATE_FILE, 'w') as f:
                        json.dump(state, f, indent=2)
                        
            except Exception as exc:
                print(f"{app_name} exception: {exc}")

    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

    print(f"Finished. Found prompts for {count} apps.")

if __name__ == "__main__":
    main()

