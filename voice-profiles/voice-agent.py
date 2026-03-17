#!/usr/bin/env python3
"""
Voice Chat Agent - Jarvis with full campaign access
Uses OpenRouter (Hunter Alpha) with campaign context and file access
"""

import json, os, subprocess, sys, time, urllib.request, urllib.error

# Config
API_URL = "http://192.168.0.222:1234/v1/chat/completions"
MODEL = "nvidia-nemotron-3-nano-4b"
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
VOICE = "en-US-AndrewMultilingualNeural"
CHAT_DIR = os.path.expanduser("~/voice-profiles/chat")

os.makedirs(CHAT_DIR, exist_ok=True)

# Load campaign context
def load_campaign_context():
    ctx = "=== CAMPAIGN CONTEXT ===\n"
    
    # README summary
    readme = os.path.join(WORKSPACE, "campaign/README.md")
    if os.path.exists(readme):
        with open(readme) as f:
            ctx += f.read()[:2000] + "\n\n"
    
    # Session list
    sessions_dir = os.path.join(WORKSPACE, "campaign/sessions")
    if os.path.isdir(sessions_dir):
        files = sorted(os.listdir(sessions_dir))
        ctx += f"SESSIONS: {', '.join(f for f in files if f.endswith('.md'))}\n\n"
    
    # NPC files
    npc_dir = os.path.join(WORKSPACE, "campaign/npcs")
    if os.path.isdir(npc_dir):
        files = os.listdir(npc_dir)
        ctx += f"NPC FILES: {', '.join(f for f in files if f.endswith('.md'))}\n\n"
    
    ctx += "=== END CONTEXT ==="
    return ctx

CAMPAIGN_CONTEXT = load_campaign_context()

# Dice rolling
import random
def roll_dice(notation):
    """Roll dice like '1d20', '2d6+3', '4d6kh3' (keep highest 3)"""
    try:
        notation = notation.lower().replace(' ', '')
        
        # Handle keep highest/lowest
        keep_highest = None
        keep_lowest = None
        if 'kh' in notation:
            parts = notation.split('kh')
            notation = parts[0]
            keep_highest = int(parts[1])
        elif 'kl' in notation:
            parts = notation.split('kl')
            notation = parts[0]
            keep_lowest = int(parts[1])
        
        # Handle modifier
        modifier = 0
        if '+' in notation:
            parts = notation.split('+')
            notation = parts[0]
            modifier = int(parts[1])
        elif '-' in notation and notation.count('-') > 0 and not notation.startswith('-'):
            # Only split on minus if it's not at the start (for negative modifiers)
            idx = notation.rfind('-')
            if idx > 0:
                modifier = -int(notation[idx+1:])
                notation = notation[:idx]
        
        # Parse XdY
        if 'd' not in notation:
            return None
        parts = notation.split('d')
        num_dice = int(parts[0]) if parts[0] else 1
        die_size = int(parts[1])
        
        # Roll
        rolls = [random.randint(1, die_size) for _ in range(num_dice)]
        
        # Keep highest/lowest
        if keep_highest and len(rolls) > keep_highest:
            rolls_sorted = sorted(rolls, reverse=True)
            kept = rolls_sorted[:keep_highest]
            total = sum(kept) + modifier
            return {'rolls': rolls, 'kept': kept, 'total': total, 'modifier': modifier, 'dice': f'{num_dice}d{die_size}kh{keep_highest}'}
        elif keep_lowest and len(rolls) > keep_lowest:
            rolls_sorted = sorted(rolls)
            kept = rolls_sorted[:keep_lowest]
            total = sum(kept) + modifier
            return {'rolls': rolls, 'kept': kept, 'total': total, 'modifier': modifier, 'dice': f'{num_dice}d{die_size}kl{keep_lowest}'}
        else:
            total = sum(rolls) + modifier
            return {'rolls': rolls, 'total': total, 'modifier': modifier, 'dice': f'{num_dice}d{die_size}'}
    except Exception as e:
        return None

# Read a campaign file
def read_campaign_file(filename):
    # Try direct path
    path = os.path.join(WORKSPACE, "campaign", filename)
    if not os.path.exists(path):
        # Try sessions subfolder
        path = os.path.join(WORKSPACE, "campaign/sessions", filename)
    if not os.path.exists(path):
        # Try npcs subfolder
        path = os.path.join(WORKSPACE, "campaign/npcs", filename)
    
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
            return content[:4000]  # Limit for voice context
    return None

# System prompt
SYSTEM_PROMPT = f"""You are Jarvis, a voice-activated AI assistant for Kevin (xXBairdiXx).

RULES FOR VOICE:
- Keep responses to 2-4 sentences maximum
- Natural conversational tone, no markdown/bullets/headers
- When reading campaign files, summarize verbally
- If asked for details, give highlights and offer to go deeper
- Use dramatic tones when reading NPC dialogue or descriptions

You can read campaign files by using the read_file tool. Available files:
- session-01.md through session-20.md (in campaign/sessions/)
- npc-reference.md and npc-reference-expanded.md (in campaign/npcs/)
- README.md (campaign overview)

{CAMPAIGN_CONTEXT}"""

# Conversation history
history = [{"role": "system", "content": SYSTEM_PROMPT}]

def call_openrouter(messages):
    """Call LM Studio API"""
    data = json.dumps({
        "model": MODEL,
        "messages": messages,
        "max_tokens": 400,
        "temperature": 0.7
    }).encode()
    
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

def text_to_speech(text, loop):
    """Generate and play speech"""
    outfile = os.path.join(CHAT_DIR, f"reply_{loop}.mp3")
    subprocess.run([
        "edge-tts", "--voice", VOICE,
        "--text", text,
        "--write-media", outfile
    ], capture_output=True, timeout=15)
    
    subprocess.run(["termux-media-player", "play", outfile], capture_output=True)
    return outfile

def estimate_playback(text):
    """Estimate playback duration in seconds"""
    return len(text) / 12 + 2

def main():
    print("🎙️ JARVIS - Voice Agent with Campaign Access")
    print("============================================")
    print(f"Model: {MODEL}")
    print(f"Voice: {VOICE}")
    print(f"Campaign: {len(CAMPAIGN_CONTEXT)} chars loaded")
    print("Ctrl+C to stop\n")
    
    # Startup
    text_to_speech("Voice agent online. I have full access to The Veil's Edge campaign. What do you need?", 0)
    time.sleep(4)
    
    loop = 0
    cooldown_until = 0
    
    while True:
        loop += 1
        
        # Wait for cooldown (prevent picking up own TTS)
        now = time.time()
        if now < cooldown_until:
            wait_time = cooldown_until - now
            print(f"   ⏳ Cooldown {wait_time:.0f}s...")
            time.sleep(wait_time)
        
        print(f"🔴 Listening... (turn {loop})")
        
        # Speech to text
        result = subprocess.run(["termux-speech-to-text"], capture_output=True, text=True, timeout=30)
        text = result.stdout.strip()
        
        if not text or len(text) < 8:
            print(f"   ⏭️  Too short ({len(text)} chars), ignoring...")
            continue
        
        # Check if speech matches our last response (hearing our own TTS)
        last_reply = history[-1]["content"] if history[-1]["role"] == "assistant" else ""
        if last_reply:
            # Simple similarity: if speech contains significant chunks of our last response
            text_lower = text.lower().strip()
            reply_lower = last_reply.lower().strip()
            # Check if >40% of the speech words match our last response
            text_words = set(text_lower.split())
            reply_words = set(reply_lower.split())
            if reply_words:
                overlap = len(text_words & reply_words) / len(text_words) if text_words else 0
                if overlap > 0.4:
                    print(f"   🔄 Echo detected ({overlap:.0%} match), ignoring own voice...")
                    continue
        
        print(f"📝 You: {text}")
        
        # Check if user wants to read a file
        file_content = None
        lower = text.lower()
        if "session" in lower:
            import re
            match = re.search(r'session\s*(\d+)', lower)
            if match:
                num = int(match.group(1))
                file_content = read_campaign_file(f"session-{num:02d}.md")
                if file_content:
                    text += f"\n\n[File content loaded: session-{num:02d}.md - {len(file_content)} chars. Summarize this verbally.]"
        
        # Add to history
        history.append({"role": "user", "content": text})
        
        # Keep history manageable (system + last 10 exchanges)
        if len(history) > 21:
            history[:] = [history[0]] + history[-20:]
        
        print("🤔 Thinking...")
        
        # Get response
        reply = call_openrouter(history)
        
        if not reply:
            print("❌ No response")
            history.pop()  # Remove failed message
            continue
        
        # Strip thinking tags (GLM uses <think>... blocks)
        import re
        # Remove <think>... blocks (greedy to catch all)
        reply_clean = re.sub(r'<think>.*？', '', reply, flags=re.DOTALL).strip()
        # If closing tag exists, grab only text after it
        if '</think>' in reply:
            reply_clean = reply.split('</think>')[-1].strip()
        
        if not reply_clean:
            print("⚠️  Empty response after stripping thinking tags")
            history.pop()
            continue
        
        print(f"💬 Jarvis: {reply_clean}")
        
        # Add to history (use clean version)
        history.append({"role": "assistant", "content": reply_clean})
        
        # Speak
        text_to_speech(reply_clean, loop)
        playback_time = estimate_playback(reply_clean)
        time.sleep(playback_time)
        
        # Cooldown to prevent picking up own voice (longer pause helps)
        cooldown_until = time.time() + 5
        
        print("✅\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🔇 Voice chat ended.")
