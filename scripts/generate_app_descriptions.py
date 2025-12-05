#!/usr/bin/env python3
"""
Generate one-sentence descriptions for apps by analyzing their code, metadata, and screenshots.
Updates the CSV file with the generated descriptions.
"""
import json
import csv
import os
import re
from pathlib import Path
from typing import Optional, Dict, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APPS_DIR = os.path.join(BASE_DIR, "apps")
STATE_FILE = os.path.join(BASE_DIR, "app-review", "apps-state.json")
CSV_FILE = os.path.join(BASE_DIR, "app-review", "apps.csv")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "app-review", "public", "apps")

def read_metadata(app_path: str) -> Optional[Dict[str, str]]:
    """Read metadata.ts file from app submodule"""
    metadata_path = os.path.join(app_path, "mini-app", "lib", "metadata.ts")
    if not os.path.exists(metadata_path):
        return None
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metadata = {}
        # Extract title
        title_match = re.search(r'export const title\s*=\s*["\']([^"\']+)["\']', content)
        if title_match:
            metadata['title'] = title_match.group(1)
        
        # Extract description
        desc_match = re.search(r'export const description\s*=\s*["\']([^"\']+)["\']', content)
        if desc_match:
            metadata['description'] = desc_match.group(1)
        
        return metadata if metadata else None
    except Exception as e:
        print(f"Error reading metadata for {app_path}: {e}")
        return None

def read_page_content(app_path: str) -> Optional[str]:
    """Read main page.tsx content to understand app functionality"""
    page_path = os.path.join(app_path, "mini-app", "app", "page.tsx")
    if not os.path.exists(page_path):
        return None
    
    try:
        with open(page_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading page.tsx for {app_path}: {e}")
        return None

def analyze_code_content(page_content: str) -> Dict[str, any]:
    """Analyze page content to extract key features"""
    features = {
        'has_buttons': bool(re.search(r'Button|button', page_content)),
        'has_input': bool(re.search(r'Input|input|TextField|textfield', page_content)),
        'has_form': bool(re.search(r'Form|form', page_content)),
        'has_game': bool(re.search(r'game|Game|play|Play|score|Score', page_content, re.I)),
        'has_crypto': bool(re.search(r'crypto|Crypto|token|Token|wallet|Wallet|ethereum|Ethereum|bitcoin|Bitcoin', page_content, re.I)),
        'has_quiz': bool(re.search(r'quiz|Quiz|question|Question|answer|Answer', page_content, re.I)),
        'has_tracker': bool(re.search(r'track|Track|monitor|Monitor|log|Log', page_content, re.I)),
        'has_calculator': bool(re.search(r'calc|Calc|calculate|Calculate|math|Math', page_content, re.I)),
        'has_chat': bool(re.search(r'chat|Chat|message|Message|conversation|Conversation', page_content, re.I)),
        'has_ai': bool(re.search(r'ai|AI|artificial|Artificial|intelligence|Intelligence|assistant|Assistant', page_content, re.I)),
    }
    return features

def get_screenshot_path(app_name: str) -> Optional[str]:
    """Get path to screenshot if it exists"""
    screenshot_dir = os.path.join(SCREENSHOTS_DIR, app_name)
    if not os.path.exists(screenshot_dir):
        return None
    
    # Look for screenshot-1.png or any screenshot
    screenshot_path = os.path.join(screenshot_dir, "screenshot-1.png")
    if os.path.exists(screenshot_path):
        return screenshot_path
    
    # Check for any screenshot
    for file in os.listdir(screenshot_dir):
        if file.endswith('.png') and 'icon' not in file.lower() and 'logo' not in file.lower():
            return os.path.join(screenshot_dir, file)
    
    return None

def extract_key_info_from_prompt(prompt_text: str) -> Dict[str, any]:
    """Extract key information from prompt text"""
    prompt_lower = prompt_text.lower()
    info = {
        'is_game': any(word in prompt_lower for word in ['game', 'play', 'score', 'win', 'lose', 'puzzle', 'quiz']),
        'is_crypto': any(word in prompt_lower for word in ['crypto', 'bitcoin', 'ethereum', 'defi', 'dao', 'token', 'wallet', 'blockchain']),
        'is_tracker': any(word in prompt_lower for word in ['track', 'monitor', 'log', 'record', 'watch']),
        'is_calculator': any(word in prompt_lower for word in ['calc', 'calculate', 'compute', 'math']),
        'is_ai': any(word in prompt_lower for word in ['ai', 'artificial intelligence', 'assistant', 'chatbot', 'generate']),
        'is_quiz': any(word in prompt_lower for word in ['quiz', 'question', 'test', 'trivia']),
        'main_action': None
    }
    
    # Extract main action verb
    action_patterns = [
        r'(?:create|build|make|generate|design)\s+(?:a|an)\s+([^.!?]+)',
        r'(?:app|tool|application)\s+(?:that|which)\s+([^.!?]+)',
        r'(?:help|allows?|lets?|enables?)\s+(?:users?|you)\s+(?:to\s+)?([^.!?]+)',
    ]
    
    for pattern in action_patterns:
        match = re.search(pattern, prompt_text, re.I)
        if match:
            info['main_action'] = match.group(1).strip()
            break
    
    return info

def generate_categories(
    app_name: str,
    title: str,
    description: str,
    metadata_desc: Optional[str],
    page_content: Optional[str],
    features: Dict[str, any],
    state_data: Optional[Dict]
) -> List[str]:
    """Generate categories/tags for the app"""
    categories = set()
    title_lower = title.lower()
    desc_lower = description.lower() if description else ""
    app_name_lower = app_name.lower()
    
    # Extract prompt text for analysis
    prompt_text = ""
    if state_data:
        prompts = state_data.get('prompts') or []
        if prompts and len(prompts) > 0:
            prompt_text = prompts[0].get('text', '').lower() if isinstance(prompts[0], dict) else str(prompts[0]).lower()
        elif state_data.get('prompt'):
            prompt_text = state_data.get('prompt', '').lower()
    
    combined_text = f"{title_lower} {desc_lower} {app_name_lower} {prompt_text}".lower()
    
    # Game categories (prioritize games)
    game_keywords = ['game', 'play', 'score', 'win', 'lose', 'puzzle', 'arcade', 'casual', 'strategy', 'gaming']
    is_game = any(keyword in combined_text for keyword in game_keywords) or features.get('has_game')
    
    if is_game:
        if '2048' in combined_text or 'puzzle' in combined_text:
            categories.add('Puzzle')
        elif 'quiz' in combined_text or features.get('has_quiz'):
            categories.add('Quiz')
            categories.add('Education')
        elif 'card' in combined_text or 'blackjack' in combined_text or 'poker' in combined_text:
            categories.add('Card Game')
        elif 'slot' in combined_text or 'casino' in combined_text:
            categories.add('Casino')
        elif 'mario' in combined_text or 'platform' in combined_text or 'jump' in combined_text:
            categories.add('Platformer')
        elif 'shooter' in combined_text or 'shoot' in combined_text:
            categories.add('Shooter')
        elif 'snake' in combined_text or 'classic' in combined_text:
            categories.add('Classic')
        else:
            categories.add('Game')
    
    # Crypto/DeFi categories (only if not already a game)
    crypto_keywords = ['crypto', 'bitcoin', 'ethereum', 'defi', 'dao', 'token', 'wallet', 'blockchain', 'nft', 'airdrop', 'web3']
    is_crypto = any(keyword in combined_text for keyword in crypto_keywords) or features.get('has_crypto')
    
    if is_crypto and not is_game:
        categories.add('Crypto')
        
        if 'defi' in combined_text or 'yield' in combined_text or 'liquidity' in combined_text or 'staking' in combined_text:
            categories.add('DeFi')
        if 'tracker' in combined_text or 'monitor' in combined_text or features.get('has_tracker'):
            categories.add('Tracker')
        if 'calculator' in combined_text or 'calc' in combined_text or features.get('has_calculator'):
            categories.add('Calculator')
        if 'alert' in combined_text or 'notification' in combined_text:
            categories.add('Alert')
        if 'portfolio' in combined_text or 'wallet' in combined_text:
            categories.add('Portfolio')
        if 'trading' in combined_text or 'trade' in combined_text:
            categories.add('Trading')
        if 'airdrop' in combined_text:
            categories.add('Airdrop')
    
    # AI/Assistant categories (be more specific)
    ai_keywords = ['ai-powered', 'ai assistant', 'artificial intelligence', 'chatbot', 'gpt', 'openai', 'claude', 'llm']
    ai_context = any(keyword in combined_text for keyword in ai_keywords)
    has_ai_feature = features.get('has_ai')
    
    # Only add AI if it's clearly an AI app, not just because it generates something
    if ai_context or (has_ai_feature and ('assistant' in combined_text or 'chatbot' in combined_text)):
        categories.add('AI')
        if 'chat' in combined_text or features.get('has_chat'):
            categories.add('Chat')
    
    # Generator category (separate from AI, only if it's clearly a generator tool)
    generator_keywords = ['generator', 'generate', 'creator', 'maker', 'builder']
    is_generator = any(keyword in combined_text for keyword in generator_keywords)
    # Don't add generator if it's already categorized as something else specific
    if is_generator and not (is_game or is_crypto):
        if ai_context:
            categories.add('AI Generator')
        else:
            categories.add('Generator')
    
    # Productivity categories
    if 'tracker' in combined_text or features.get('has_tracker'):
        if 'habit' in combined_text or 'fitness' in combined_text or 'health' in combined_text:
            categories.add('Health')
            categories.add('Fitness')
        elif 'task' in combined_text or 'todo' in combined_text:
            categories.add('Productivity')
        elif 'budget' in combined_text or 'finance' in combined_text:
            categories.add('Finance')
        else:
            categories.add('Tracker')
    
    # Education categories
    education_keywords = ['learn', 'study', 'education', 'tutorial', 'lesson', 'course', 'flashcard']
    if any(keyword in combined_text for keyword in education_keywords):
        categories.add('Education')
        if 'language' in combined_text or 'learn' in combined_text:
            categories.add('Language Learning')
    
    # Social categories (be more specific)
    social_keywords = ['social media', 'share', 'community', 'feed', 'post', 'social network']
    if any(keyword in combined_text for keyword in social_keywords):
        categories.add('Social')
    # Chat is separate and more specific
    if 'chat' in combined_text and 'chatbot' not in combined_text:
        if 'ai' in combined_text or 'assistant' in combined_text:
            categories.add('AI Chat')
        else:
            categories.add('Chat')
    
    # Finance categories
    finance_keywords = ['finance', 'budget', 'investment', 'trading', 'portfolio', 'money']
    if any(keyword in combined_text for keyword in finance_keywords) and 'crypto' not in combined_text:
        categories.add('Finance')
    
    # Health/Fitness categories
    health_keywords = ['health', 'fitness', 'workout', 'exercise', 'sleep', 'meditation', 'wellness']
    if any(keyword in combined_text for keyword in health_keywords):
        categories.add('Health')
        categories.add('Fitness')
    
    # Utility categories
    utility_keywords = ['converter', 'calculator', 'tool', 'utility', 'helper']
    if any(keyword in combined_text for keyword in utility_keywords) and not categories:
        categories.add('Utility')
    
    # Entertainment categories
    if 'entertainment' in combined_text or ('fun' in combined_text and not categories):
        categories.add('Entertainment')
    
    # If no categories found, try to infer from title/name
    if not categories:
        if any(char.isdigit() for char in app_name) and len(app_name) < 10:
            # Likely a default/generic app
            categories.add('Other')
        else:
            # Try to infer from common patterns
            if 'mini' in app_name_lower or 'app' in app_name_lower:
                categories.add('Other')
            else:
                categories.add('Utility')
    
    # Sort categories for consistency
    return sorted(list(categories))

def clean_description(description: str) -> str:
    """Clean and truncate description to one sentence, max 150 chars"""
    if not description:
        return ""
    
    # Remove extra whitespace
    description = ' '.join(description.split())
    
    # If too long, try to find the first sentence
    if len(description) > 150:
        # Split by sentence endings
        sentences = re.split(r'([.!?])\s+', description)
        if len(sentences) > 1:
            # Take first sentence
            first_sentence = sentences[0] + (sentences[1] if len(sentences) > 1 else '.')
            if len(first_sentence) <= 150:
                return first_sentence.strip()
        
        # If still too long, truncate at word boundary
        words = description.split()
        truncated = []
        for word in words:
            if len(' '.join(truncated + [word])) <= 147:  # Leave room for "..."
                truncated.append(word)
            else:
                break
        if truncated:
            result = ' '.join(truncated)
            if not result.endswith(('.', '!', '?')):
                result += '...'
            return result
    
    return description.strip()

def generate_description(
    app_name: str,
    title: str,
    metadata_desc: Optional[str],
    page_content: Optional[str],
    features: Dict[str, any],
    state_data: Optional[Dict]
) -> str:
    """Generate a one-sentence description for the app"""
    
    # Use existing description from metadata if it's good (not default)
    if metadata_desc and metadata_desc.strip():
        default_descriptions = [
            "This app was created by the Mini App Factory!",
            "An amazing app built with Mini App Factory.",
            "Mini App Factory App"
        ]
        if metadata_desc not in default_descriptions and len(metadata_desc) > 10:
            return metadata_desc.strip()
    
    # Use description from state if available
    if state_data and state_data.get('description'):
        desc = state_data.get('description', '').strip()
        if desc and len(desc) > 10:
            return desc
    
    # Try to extract from prompts
    prompt_text = None
    if state_data:
        prompts = state_data.get('prompts') or []
        if prompts and len(prompts) > 0:
            prompt_text = prompts[0].get('text', '') if isinstance(prompts[0], dict) else str(prompts[0])
        elif state_data.get('prompt'):
            prompt_text = state_data.get('prompt')
    
    if prompt_text and len(prompt_text) > 20:
        prompt_info = extract_key_info_from_prompt(prompt_text)
        
        # Generate description from prompt
        # Try to create a concise summary from the first sentence or key phrase
        sentences = re.split(r'[.!?]\s+', prompt_text)
        if sentences:
            # Use first sentence if it's reasonable length
            first_sentence = sentences[0].strip()
            # Clean up common prefixes
            first_sentence = re.sub(r'^(?:create|build|make|design|code|develop)\s+(?:a|an|the)\s+', '', first_sentence, flags=re.I)
            first_sentence = re.sub(r'^(?:an?)\s+', '', first_sentence, flags=re.I)
            first_sentence = re.sub(r'^(?:app|tool|application|mini app)\s+(?:that|which)\s+', '', first_sentence, flags=re.I)
            
            # If first sentence is too long, try to extract key phrase
            if len(first_sentence) > 150:
                # Try to find a shorter key phrase
                key_phrases = re.findall(r'(?:that|which)\s+([^.!?]{20,120})', prompt_text, re.I)
                if key_phrases:
                    first_sentence = key_phrases[0].strip()
                else:
                    # Truncate intelligently
                    words = first_sentence.split()
                    if len(words) > 20:
                        first_sentence = ' '.join(words[:20])
            
            # Capitalize first letter
            if first_sentence and len(first_sentence) > 15:
                first_sentence = first_sentence[0].upper() + first_sentence[1:] if len(first_sentence) > 1 else first_sentence.upper()
                # Ensure it ends with period
                if not first_sentence.endswith(('.', '!', '?')):
                    first_sentence += '.'
                # Limit to one sentence max 150 chars
                if len(first_sentence) <= 150:
                    return first_sentence
    
    # Generate based on title and features
    title_lower = title.lower()
    
    # Game apps
    if features.get('has_game') or 'game' in title_lower or '2048' in title_lower or 'puzzle' in title_lower:
        if '2048' in title_lower:
            return "A classic 2048 number puzzle game where you combine tiles to reach the 2048 tile."
        elif 'puzzle' in title_lower:
            return f"A fun puzzle game featuring {title}."
        elif 'quiz' in title_lower or features.get('has_quiz'):
            return f"An interactive quiz game about {title.replace(' Quiz', '').replace('Quiz ', '')}."
        else:
            return f"A fun and engaging game: {title}."
    
    # Crypto/DeFi apps
    if features.get('has_crypto') or 'crypto' in title_lower or 'defi' in title_lower or 'dao' in title_lower:
        if 'tracker' in title_lower or features.get('has_tracker'):
            return f"Track and monitor {title.lower().replace(' tracker', '').replace('tracker ', '')} in real-time."
        elif 'calculator' in title_lower or features.get('has_calculator'):
            return f"Calculate and analyze {title.lower().replace(' calculator', '').replace('calc', '')}."
        elif 'alert' in title_lower:
            return f"Receive alerts and notifications for {title.lower().replace(' alert', '')}."
        else:
            return f"A DeFi and crypto tool for {title.lower()}."
    
    # AI/Assistant apps
    if features.get('has_ai') or 'ai' in title_lower or 'assistant' in title_lower:
        if 'chat' in title_lower or features.get('has_chat'):
            return f"An AI-powered chat assistant for {title.lower().replace(' chat', '').replace('assistant', '')}."
        else:
            return f"An AI-powered tool that helps with {title.lower()}."
    
    # Tracker apps
    if features.get('has_tracker') or 'tracker' in title_lower:
        return f"Track and monitor your {title.lower().replace(' tracker', '').replace('tracker ', '')}."
    
    # Calculator apps
    if features.get('has_calculator') or 'calc' in title_lower or 'calculator' in title_lower:
        return f"Calculate and compute {title.lower().replace(' calculator', '').replace('calc', '')}."
    
    # Quiz apps
    if features.get('has_quiz') or 'quiz' in title_lower:
        return f"Test your knowledge with interactive quizzes about {title.lower().replace(' quiz', '')}."
    
    # Fitness/Health apps
    if 'fitness' in title_lower or 'health' in title_lower or 'workout' in title_lower:
        return f"Track and improve your {title.lower()} with personalized plans and progress monitoring."
    
    # Food apps
    if 'food' in title_lower or 'recipe' in title_lower or 'cooking' in title_lower:
        return f"Discover and explore {title.lower()} with recipes, ratings, and recommendations."
    
    # Try to infer from component names in page content
    if page_content:
        # Look for component imports that might indicate functionality
        component_matches = re.findall(r'from\s+["\']@/components/([^"\']+)["\']', page_content)
        if component_matches:
            components = [c.lower() for c in component_matches]
            if any('game' in c for c in components):
                return f"A fun game: {title}."
            if any('quiz' in c for c in components):
                return f"An interactive quiz about {title.replace(' Quiz', '').replace('Quiz ', '')}."
            if any('tracker' in c or 'track' in c for c in components):
                return f"Track and monitor your {title.lower().replace(' tracker', '').replace('tracker ', '')}."
            if any('calc' in c or 'calculator' in c for c in components):
                return f"Calculate and analyze {title.lower().replace(' calculator', '').replace('calc', '')}."
    
    # Default fallback
    if title and title != "Mini App Factory App":
        # Try to make it more descriptive
        title_words = title.split()
        if len(title_words) > 1:
            return f"A {title.lower()} app that helps you manage and interact with {title_words[-1].lower()}."
        return f"A useful app for {title.lower()}."
    else:
        return f"A mini app for {app_name.replace('-', ' ')}."

def process_app(app_name: str, state_data: Optional[Dict]) -> tuple[Optional[str], List[str]]:
    """Process a single app and generate description and categories"""
    app_path = os.path.join(APPS_DIR, app_name)
    
    if not os.path.exists(app_path):
        return None, []
    
    # Read metadata
    metadata = read_metadata(app_path)
    title = metadata.get('title') if metadata else state_data.get('title') if state_data else app_name
    metadata_desc = metadata.get('description') if metadata else None
    
    # Read page content
    page_content = read_page_content(app_path)
    features = analyze_code_content(page_content) if page_content else {}
    
    # Generate description
    description = generate_description(
        app_name=app_name,
        title=title,
        metadata_desc=metadata_desc,
        page_content=page_content,
        features=features,
        state_data=state_data
    )
    
    # Clean and ensure it's one sentence
    if description:
        description = clean_description(description)
    
    # Generate categories
    categories = generate_categories(
        app_name=app_name,
        title=title,
        description=description or "",
        metadata_desc=metadata_desc,
        page_content=page_content,
        features=features,
        state_data=state_data
    )
    
    return description, categories

def update_csv_with_descriptions():
    """Read CSV, generate descriptions, and update CSV"""
    # Load state data
    state_data = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
    
    # Read existing CSV
    rows = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames) if reader.fieldnames else []
            rows = list(reader)
    else:
        print(f"CSV file not found: {CSV_FILE}")
        return
    
    # Ensure 'description' and 'categories' fields exist
    if 'description' not in fieldnames:
        fieldnames.append('description')
    if 'categories' not in fieldnames:
        fieldnames.append('categories')
    
    # Process each app
    updated_count = 0
    for row in rows:
        app_name = row.get('name')
        if not app_name:
            continue
        
        # Check if description needs updating
        existing_desc = row.get('description', '').strip()
        existing_categories = row.get('categories', '').strip()
        needs_update_desc = False
        needs_update_categories = False
        
        # Update if no description or description is too long (>150 chars) or too short (<10 chars)
        if not existing_desc or len(existing_desc) < 10:
            needs_update_desc = True
        elif len(existing_desc) > 150:
            # Clean up long descriptions
            cleaned = clean_description(existing_desc)
            if cleaned != existing_desc:
                row['description'] = cleaned
                updated_count += 1
                print(f"✓ {app_name}: {cleaned[:100]}...")
            # Still generate categories even if description was cleaned
            needs_update_categories = not existing_categories
        elif existing_desc and len(existing_desc) > 10:
            # Description is good, but check if we need categories
            needs_update_categories = not existing_categories
        
        # Generate description and categories if needed
        state_info = state_data.get(app_name)
        description = None
        categories = []
        
        if needs_update_desc or needs_update_categories:
            description, categories = process_app(app_name, state_info)
        
        if needs_update_desc and description:
            row['description'] = description
            updated_count += 1
            print(f"✓ {app_name}: {description}")
        
        if needs_update_categories and categories:
            row['categories'] = ', '.join(categories)
            if not needs_update_desc:  # Only print if we didn't already print for description
                print(f"✓ {app_name}: Categories: {', '.join(categories)}")
            updated_count += 1
    
    # Write updated CSV
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✅ Updated {updated_count} app descriptions in {CSV_FILE}")

if __name__ == "__main__":
    update_csv_with_descriptions()

