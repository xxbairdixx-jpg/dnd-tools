#!/usr/bin/env python3
"""Voice DM - Clean version with HTTP VTT commands and PTT input"""
import json, os, subprocess, time, urllib.request, re, random, asyncio, websockets, threading, queue

# Config
API = "http://192.168.0.222:1234/v1/chat/completions"
MODEL = "zai-org/glm-4.6v-flash"
WS = os.path.expanduser("~/.openclaw/workspace")
VOICE = "en-US-AndrewMultilingualNeural"
CHAT = os.path.expanduser("~/voice-profiles/chat")
os.makedirs(CHAT, exist_ok=True)

# PTT queue
speech_q = queue.Queue()

# D&D Rules
RULES = """DC: 5 Easy, 10 Medium, 15 Hard, 20 VHard, 25 Extreme
Skills: Athletics(STR), Acrobatics(DEX), Stealth(DEX), Perception(WIS), Investigation(INT), Persuasion(CHA), Intimidation(CHA), Deception(CHA), Insight(WIS), Arcana(INT)
Conditions: Poisoned(disadvantage attacks/checks), Prone(melee adv/ranged disadv), Stunned(auto-fail STR/DEX saves), Frightened(disadvantage), Restrained(speed 0, disadv attacks)
Short Rest: spend Hit Dice, warlock slots recover. Long Rest: full HP, all slots."""

# Campaign context
def load_ctx():
    ctx = ""
    p = os.path.join(WS, "campaign/README.md")
    if os.path.exists(p):
        with open(p) as f: ctx += f.read()[:2000]
    return ctx

CAMPAIGN = load_ctx()

SYSTEM = f"""You are Jarvis, voice DM for "The Veil's Edge" D&D 5e campaign.
- Keep responses 2-4 sentences for voice. No markdown.
- Call for ability checks when player describes actions. "Roll Perception"
- Narrate outcomes based on dice rolls vs DC/AC
- Use [VTT:ADD name type hp ac x y] to add tokens to the map
- Use [VTT:DAMAGE name amount] when enemies take damage
- Use [VTT:HEAL name amount] for healing
- Use [VTT:MOVE name x y] to move tokens (pixel coords, 50px grid)
- Use [VTT:INITIATIVE] to roll initiative
- Use [VTT:NEXT] to advance turns
- Use [VTT:CONDITION name condition] to apply conditions

{RULES}

Campaign: {CAMPAIGN}
"""

history = [{"role": "system", "content": SYSTEM}]

# VTT command via HTTP
def vtt(action, **params):
    try:
        data = json.dumps({"action": action, **params}).encode()
        req = urllib.request.Request('http://localhost:9000/command', data=data, headers={'Content-Type': 'application/json'}, method='POST')
        urllib.request.urlopen(req, timeout=2)
        print(f"   📡 VTT: {action}")
    except Exception as e:
        print(f"   ⚠️ VTT error: {e}")

def get_vtt_state():
    """Get current VTT state"""
    try:
        req = urllib.request.Request('http://localhost:9000/state')
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read())
    except:
        return None

def format_vtt_state(state):
    """Format VTT state as text for the DM"""
    if not state or not state.get('tokens'):
        return "The map is currently empty - no tokens placed."
    lines = [f"VTT MAP STATE (Round {state.get('round', 1)}):"]
    for t in state['tokens']:
        cond = f" [{', '.join(t['conditions'])}]" if t.get('conditions') else ""
        lines.append(f"  - {t['name']} ({t['type']}): HP {t['hp']}/{t['maxHp']}, AC {t['ac']}, position ({t.get('gridX',0)},{t.get('gridY',0)}){cond}")
    if state.get('initiativeOrder'):
        lines.append(f"Initiative: {' → '.join(state['initiativeOrder'])}")
    return '\n'.join(lines)

def parse_vtt(text):
    for m in re.finditer(r'\[VTT:ADD\s+(\S+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\]', text):
        n,t,hp,a,x,y = m.groups()
        vtt('add_token', name=n.replace('_',' '), type=t, hp=int(hp), ac=int(a), x=int(x), y=int(y))
    for m in re.finditer(r'\[VTT:DAMAGE\s+(\S+)\s+(\d+)\]', text):
        n,a = m.groups()
        vtt('damage_token', name=n.replace('_',' '), amount=int(a))
    for m in re.finditer(r'\[VTT:HEAL\s+(\S+)\s+(\d+)\]', text):
        n,a = m.groups()
        vtt('heal_token', name=n.replace('_',' '), amount=int(a))
    for m in re.finditer(r'\[VTT:MOVE\s+(\S+)\s+(\d+)\s+(\d+)\]', text):
        n,x,y = m.groups()
        vtt('move_token', name=n.replace('_',' '), x=int(x), y=int(y))
    for m in re.finditer(r'\[VTT:CONDITION\s+(\S+)\s+(\w+)\]', text):
        n,c = m.groups()
        vtt('set_condition', name=n.replace('_',' '), condition=c)
    if '[VTT:INITIATIVE]' in text: vtt('roll_initiative')
    if '[VTT:NEXT]' in text: vtt('next_turn')
    # QUERY is handled by state injection before the LLM call, but handle here too
    if '[VTT:QUERY]' in text:
        state = get_vtt_state()
        if state:
            print(f"   📊 Map: {len(state.get('tokens',[]))} tokens")
    return re.sub(r'\[VTT:[^\]]+\]', '', text).strip()

# TTS
def speak(text, loop=0):
    f = os.path.join(CHAT, f"r_{loop}.mp3")
    subprocess.run(["edge-tts", "--voice", VOICE, "--text", text, "--write-media", f], capture_output=True, timeout=15)
    subprocess.run(["termux-media-player", "play", f], capture_output=True)

# PTT WebSocket listener
async def ptt_handler(ws):
    async for msg in ws:
        try:
            data = json.loads(msg)
            if data.get('action') == 'player_speech':
                speech_q.put(data['text'])
        except: pass

async def ptt_server():
    async with websockets.serve(ptt_handler, "localhost", 9001):
        await asyncio.Future()

def run_ptt():
    asyncio.run(ptt_server())

# Main
def main():
    threading.Thread(target=run_ptt, daemon=True).start()
    print("🎙️ Voice DM v3")
    print(f"Model: {MODEL}")
    print("PTT: port 8767 | VTT commands: port 8768")
    
    speak("Voice DM online. Hold the mic button or spacebar to talk.", 0)
    time.sleep(5)
    
    turn = 0
    while True:
        turn += 1
        print(f"🔴 Waiting for PTT... (turn {turn})")
        try:
            text = speech_q.get(timeout=60)
        except queue.Empty:
            print("   ⏳ timeout")
            continue
        
        if len(text) < 5:
            print(f"   ⏭️ too short: '{text}'")
            continue
        
        print(f"📝 You: {text}")
        
        # If asking about map/tokens/position, inject VTT state
        lower = text.lower()
        if any(w in lower for w in ['map', 'token', 'how many', 'where', 'position', 'character on', 'see']):
            state = get_vtt_state()
            if state:
                state_text = format_vtt_state(state)
                text += f"\n\n[{state_text}]"
                print(f"   📊 Injected VTT state: {len(state.get('tokens',[]))} tokens")
        
        # Check for session requests
        m = re.search(r'session\s*(\d+)', text.lower())
        if m:
            path = os.path.join(WS, f"campaign/sessions/session-{int(m.group(1)):02d}.md")
            if os.path.exists(path):
                with open(path) as f: text += f"\n\n[Session content: {f.read()[:2000]}]"
        
        history.append({"role": "user", "content": text})
        if len(history) > 21: history[:] = [history[0]] + history[-20:]
        
        print("🤔 Thinking...")
        try:
            data = json.dumps({"model": MODEL, "messages": history, "max_tokens": 300}).encode()
            req = urllib.request.Request(API, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                reply = json.loads(resp.read())["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"❌ {e}")
            history.pop()
            continue
        
        # Strip thinking tags
        clean = reply
        if '</think>' in clean: clean = clean.split('</think>')[-1].strip()
        clean = re.sub(r'<think>.*？>', '', clean, flags=re.DOTALL).strip()
        if clean.startswith('<think>'): clean = ''
        
        if not clean:
            print("⚠️ empty")
            history.pop()
            time.sleep(2)
            continue
        
        # Parse VTT commands and get speakable text
        speakable = parse_vtt(clean)
        print(f"💬 DM: {speakable}")
        history.append({"role": "assistant", "content": clean})
        
        # Speak
        speak(speakable, turn)
        time.sleep(len(speakable) / 12 + 3)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\n🔇 Stopped.")
