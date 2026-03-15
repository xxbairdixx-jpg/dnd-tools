#!/usr/bin/env python3
"""
Voice DM Agent v2 - Jarvis with full D&D 5e campaign, rules, dice, VTT
"""
import json, os, subprocess, sys, time, urllib.request, urllib.error, random, re

# Config
API_URL = "http://192.168.0.222:1234/v1/chat/completions"
MODEL = "zai-org/glm-4.6v-flash"
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
VOICE = "en-US-AndrewMultilingualNeural"
CHAT_DIR = os.path.expanduser("~/voice-profiles/chat")
CHAR_DIR = os.path.expanduser("~/voice-profiles/characters")
os.makedirs(CHAT_DIR, exist_ok=True)
os.makedirs(CHAR_DIR, exist_ok=True)

# Voice assignments
VOICES = {
    "narrator": "en-US-AndrewMultilingualNeural",
    "male_warrior": "en-US-GuyNeural",
    "male_calm": "en-US-ChristopherNeural",
    "male_friendly": "en-US-BrianMultilingualNeural",
    "male_dark": "en-US-EricNeural",
    "male_lively": "en-US-RogerNeural",
    "female_warm": "en-US-EmmaMultilingualNeural",
    "female_mysterious": "en-US-MichelleNeural",
    "female_commanding": "en-US-AriaNeural",
    "female_cute": "en-US-AnaNeural",
    "ancient": "en-US-SteffanNeural",
}

# D&D 5e Rules
DND_RULES = """
## Ability Checks & DCs
DC 5 Very Easy, DC 10 Easy, DC 15 Medium, DC 20 Hard, DC 25 Very Hard, DC 30 Nearly Impossible
Skills: Athletics(STR), Acrobatics(DEX), Stealth(DEX), Investigation(INT), Perception(WIS), Insight(WIS), Persuasion(CHA), Intimidation(CHA), Deception(CHA), Medicine(WIS), Arcana(INT), Nature(INT), Religion(INT), Survival(WIS), SleightOfHand(DEX), Performance(CHA), AnimalHandling(WIS), History(INT)

## Conditions
- Blinded: auto-fail sight checks, attacks against have advantage, attacks made have disadvantage
- Charmed: can't attack charmer, charmer has advantage on social checks
- Frightened: disadvantage on checks/attacks while source in sight, can't move closer
- Grappled: speed 0
- Incapacitated: can't take actions/reactions
- Poisoned: disadvantage on attack rolls and ability checks
- Prone: can only crawl, melee attacks against have advantage, ranged have disadvantage
- Restrained: speed 0, attacks against have advantage, attacks made have disadvantage, disadvantage on DEX saves
- Stunned: incapacitated, auto-fail STR/DEX saves, attacks against have advantage
- Unconscious: incapacitated + prone, auto-fail STR/DEX saves, attacks within 5ft auto-crit

## Resting
Short Rest: 1+ hours, spend Hit Dice to heal, warlock spell slots recover
Long Rest: 6+ hours, regain all HP, half Hit Dice, all spell slots

## Death Saves
0 HP: unconscious, roll d20 each turn: 10+ = success, 9- = failure, 20 = regain 1 HP, 1 = 2 failures
3 successes: stable, 3 failures: death

## Bairdi's Spells (for reference)
Eldritch Blast: 1 action, 120ft, V+S, ranged spell attack +5, 1d10 force (2 beams at lvl 5)
Prestidigitation: 1 action, 10ft, V+S, 1 hour, minor magical effects
Fire Bolt: 1 action, 120ft, V+S, ranged spell attack +5, 1d10 fire, ignites flammable objects
Thaumaturgy: 1 action, 30ft, V, 1 minute, minor wonder (booming voice, flames flicker, tremors)
Hellish Rebuke: 1 reaction (when hit), 60ft, V+S, DEX save DC 13, 2d10 fire, half on save
Hex: 1 bonus action, 90ft, V+S+M, concentration 1hr, +1d6 necrotic on hits, disadvantage on chosen ability
Mage Armor: 1 action, touch, V+S+M, 8hr, AC = 13 + DEX (17 for Bairdi)

## Warlock 2 Features
Pact Magic: 2 spell slots (1st level), short rest recovery
Agonizing Blast: +CHA mod (+3) to Eldritch Blast damage
Armor of Shadows: at-will Mage Armor
Magical Cunning: 1/long rest, 1 min ritual, regain 1 spell slot

## Rogue 1 Features
Sneak Attack: +1d6 once/turn with finesse/ranged when advantage or ally within 5ft
Expertise: double proficiency on 2 skills
Thieves' Cant: secret language
"""

# Character system
class Character:
    def __init__(self, name=""):
        self.name = name
        self.race = ""
        self.char_class = ""
        self.level = 1
        self.abilities = {"STR":10,"DEX":10,"CON":10,"INT":10,"WIS":10,"CHA":10}
        self.max_hp = 10
        self.hp = 10
        self.temp_hp = 0
        self.ac = 10
        self.prof_bonus = 2
        self.spell_slots = {}
        self.spell_slots_used = {}
        self.hit_dice = 1
        self.hit_dice_used = 0
        self.conditions = []
        self.inventory = []
        self.gold = 0
        self.death_saves = {"successes": 0, "failures": 0}
        self.notes = ""

    def mod(self, stat):
        return (self.abilities.get(stat, 10) - 10) // 2

    def save(self):
        path = os.path.join(CHAR_DIR, f"{self.name.lower()}.json")
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)

    def load(self, name):
        path = os.path.join(CHAR_DIR, f"{name.lower()}.json")
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
                self.__dict__.update(data)
            return True
        return False

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        return self.hp <= 0

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def short_rest(self):
        # Spend hit dice to heal
        pass  # Player chooses how many

    def long_rest(self):
        self.hp = self.max_hp
        self.hit_dice_used = 0
        self.spell_slots_used = {}
        self.conditions = []
        self.death_saves = {"successes": 0, "failures": 0}

# Dice rolling
def roll_dice(notation):
    try:
        notation = notation.lower().replace(' ', '')
        keep_highest = None
        if 'kh' in notation:
            parts = notation.split('kh')
            notation = parts[0]
            keep_highest = int(parts[1])
        modifier = 0
        if '+' in notation:
            parts = notation.split('+')
            notation = parts[0]
            modifier = int(parts[1])
        elif '-' in notation and not notation.startswith('-'):
            idx = notation.rfind('-')
            if idx > 0:
                modifier = -int(notation[idx+1:])
                notation = notation[:idx]
        if 'd' not in notation:
            return None
        parts = notation.split('d')
        num = int(parts[0]) if parts[0] else 1
        size = int(parts[1])
        rolls = [random.randint(1, size) for _ in range(num)]
        if keep_highest and len(rolls) > keep_highest:
            kept = sorted(rolls, reverse=True)[:keep_highest]
            return {'rolls': rolls, 'kept': kept, 'total': sum(kept)+modifier, 'modifier': modifier}
        return {'rolls': rolls, 'total': sum(rolls)+modifier, 'modifier': modifier}
    except:
        return None

def format_roll(result):
    if not result:
        return "Invalid roll"
    s = f"Rolled: {result['rolls']}"
    if 'kept' in result:
        s += f" (kept {result['kept']})"
    if result['modifier']:
        s += f" {'+' if result['modifier']>0 else ''}{result['modifier']}"
    s += f" = **{result['total']}**"
    return s

# Load campaign context
def load_campaign_context():
    ctx = "=== THE VEIL'S EDGE CAMPAIGN ===\n"
    readme = os.path.join(WORKSPACE, "campaign/README.md")
    if os.path.exists(readme):
        with open(readme) as f:
            ctx += f.read()[:2000] + "\n\n"
    sessions_dir = os.path.join(WORKSPACE, "campaign/sessions")
    if os.path.isdir(sessions_dir):
        files = sorted(f for f in os.listdir(sessions_dir) if f.endswith('.md'))
        ctx += f"SESSIONS: {', '.join(files)}\n"
    npc_dir = os.path.join(WORKSPACE, "campaign/npcs")
    if os.path.isdir(npc_dir):
        files = [f for f in os.listdir(npc_dir) if f.endswith('.md')]
        ctx += f"NPC FILES: {', '.join(files)}\n"
    return ctx

def read_campaign_file(filename):
    for subdir in ["", "campaign/sessions/", "campaign/npcs/"]:
        path = os.path.join(WORKSPACE, subdir, filename)
        if os.path.exists(path):
            with open(path) as f:
                return f.read()[:4000]
    return None

# VTT integration
def vtt_command(action, **params):
    """Send command to VTT via HTTP (simple & reliable)"""
    try:
        cmd = json.dumps({"action": action, **params}).encode()
        req = urllib.request.Request(
            'http://localhost:8768/command',
            data=cmd,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        urllib.request.urlopen(req, timeout=2)
        print(f"   📡 VTT: {action}")
    except Exception as e:
        print(f"   ⚠️  VTT command failed: {e}")

def query_vtt_state():
    """Get current token positions from VTT"""
    try:
        req = urllib.request.Request('http://localhost:8768/state')
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read())
    except:
        return None

# Old websocket code removed - using HTTP now

def parse_and_send_vtt_commands(text):
    """Parse [VTT:...] commands from DM response and send to VTT"""
    import re
    # Parse ADD commands
    for m in re.finditer(r'\[VTT:ADD\s+(\S+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\]', text):
        name, typ, hp, ac, x, y = m.groups()
        vtt_command('add_token', name=name.replace('_', ' '), type=typ, hp=int(hp), ac=int(ac), x=int(x), y=int(y))
    
    # Parse DAMAGE commands
    for m in re.finditer(r'\[VTT:DAMAGE\s+(\S+)\s+(\d+)\]', text):
        name, amount = m.groups()
        vtt_command('damage_token', name=name.replace('_', ' '), amount=int(amount))
    
    # Parse HEAL commands
    for m in re.finditer(r'\[VTT:HEAL\s+(\S+)\s+(\d+)\]', text):
        name, amount = m.groups()
        vtt_command('heal_token', name=name.replace('_', ' '), amount=int(amount))
    
    # Parse MOVE commands
    for m in re.finditer(r'\[VTT:MOVE\s+(\S+)\s+(\d+)\s+(\d+)\]', text):
        name, x, y = m.groups()
        vtt_command('move_token', name=name.replace('_', ' '), x=int(x), y=int(y))
    
    # Parse CONDITION commands
    for m in re.finditer(r'\[VTT:CONDITION\s+(\S+)\s+(\w+)\]', text):
        name, cond = m.groups()
        vtt_command('set_condition', name=name.replace('_', ' '), condition=cond)
    
    # Parse INITIATIVE
    if '[VTT:INITIATIVE]' in text:
        vtt_command('roll_initiative')
    
    # Parse NEXT
    if '[VTT:NEXT]' in text:
        vtt_command('next_turn')
    
    # Strip VTT commands from the spoken text
    clean = re.sub(r'\[VTT:[^\]]+\]', '', text).strip()
    return clean

# TTS
def text_to_speech(text, voice=None, loop=0):
    v = voice or VOICES["narrator"]
    outfile = os.path.join(CHAT_DIR, f"reply_{loop}.mp3")
    subprocess.run(["edge-tts", "--voice", v, "--text", text, "--write-media", outfile], capture_output=True, timeout=15)
    subprocess.run(["termux-media-player", "play", outfile], capture_output=True)
    return outfile

def estimate_playback(text):
    return len(text) / 12 + 2

# State
character = Character()
combat_state = {"active": False, "round": 0, "turn": 0, "initiative": [], "enemies": {}}
npc_voices = {}

CAMPAIGN_CONTEXT = load_campaign_context()

SYSTEM_PROMPT = f"""You are Jarvis, the voice DM for "The Veil's Edge" D&D 5e campaign.

RULES:
- Keep responses to 2-4 sentences for voice
- No markdown, bullets, or headers - just natural speech
- When player describes an action, call for the appropriate check
- After dice rolls, narrate the outcome dramatically
- Use atmospheric descriptions
- Speak as NPCs with distinct voices/tones

{DND_RULES}

CAMPAIGN CONTEXT:
{CAMPAIGN_CONTEXT}

## VTT Integration
When you add enemies or NPCs to an encounter, say: [VTT:ADD name type hp ac x y]
Example: "Two goblins emerge from the shadows" → include [VTT:ADD Goblin_1 enemy 7 13 400 200] [VTT:ADD Goblin_2 enemy 7 13 450 200]

When a token takes damage: [VTT:DAMAGE name amount]
Example: [VTT:DAMAGE Goblin_1 5]

When a token is healed: [VTT:HEAL name amount]

When you want to move a token: [VTT:MOVE name x y]

When combat starts: [VTT:INITIATIVE]

When advancing turns: [VTT:NEXT]

When applying conditions: [VTT:CONDITION name condition]

These VTT commands will be sent to the battle map automatically. Players see the map on their display.

## Spatial Awareness Integration
When you need to know token positions, use: [VTT:QUERY]
The VTT will respond with token positions on the grid. Use these positions to:
- Move enemies tactically (toward players, flanking, retreating)
- Describe spatial relationships ("The goblin moves from D5 to E7, getting closer to Bairdi")
- Track distances for movement speed (30ft = 6 squares)

When moving tokens, use grid coordinates: [VTT:MOVE_GRID Goblin_1 10 5]
This moves Goblin 1 to grid position (10, 5).

The grid is 30 columns x 20 rows. Each square is 5ft.
Token positions are reported as grid coordinates (column, row).

## Gameplay Flow
When the player says what they do, determine what check is needed and ask them to roll.
Example: "I search the room" → "Roll Investigation"
Example: "I attack the goblin" → "Roll to hit"

After they report their roll, narrate what happens based on the result vs DC/AC.
When enemies appear, add them to the VTT with [VTT:ADD] commands.

## State Query Function
You can query the VTT state using:
[DM:QUERY_STATE]
This will fetch current token positions and initiative order from the battle map."""

history = [{"role": "system", "content": SYSTEM_PROMPT}]

# WebSocket listener for VTT player speech
import threading, queue
player_speech_queue = queue.Queue()

def start_ws_listener():
    """Listen for player speech from VTT"""
    import asyncio, websockets
    async def handler(websocket):
        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get('action') == 'player_speech':
                    player_speech_queue.put(data['text'])
            except:
                pass
    async def serve():
        async with websockets.serve(handler, "localhost", 8767):
            await asyncio.Future()
    try:
        asyncio.run(serve())
    except:
        pass

# Main loop
def main():
    global character, combat_state, history
    
    print("🎙️ JARVIS Voice DM v2")
    print("====================")
    print(f"Model: {MODEL}")
    print(f"Voice: {VOICE}")
    print("D&D 5e rules loaded")
    print("VTT: ws://localhost:8765")
    print("Ctrl+C to quit\n")
    
    # Start WebSocket listener for VTT PTT
    ws_thread = threading.Thread(target=start_ws_listener, daemon=True)
    ws_thread.start()
    print("📡 PTT WebSocket listening on port 8767")
    
    startup_msg = "Voice DM online. Hold the microphone button on the VTT to talk to me. Press and hold spacebar on a keyboard also works. Say 'new character' to create one, or start playing!"
    text_to_speech(startup_msg, VOICES["narrator"], 0)
    startup_wait = estimate_playback(startup_msg) + 5
    print(f"   🔊 Startup TTS, waiting {startup_wait:.0f}s to avoid echo...")
    time.sleep(startup_wait)
    cooldown_until = time.time() + 3
    
    loop = 0
    cooldown_until = 0
    
    while True:
        loop += 1
        now = time.time()
        if now < cooldown_until:
            time.sleep(cooldown_until - now)
        
        print(f"🔴 Waiting for PTT... (turn {loop})")
        
        # ONLY listen via VTT PTT button (no mic - eliminates echo)
        try:
            text = player_speech_queue.get(timeout=60)  # Wait up to 60s for input
            print(f"   📡 PTT received")
        except queue.Empty:
            print(f"   ⏳ No input, still waiting...")
            continue
        
        # PTT input is clean, no filtering needed
        
        # No echo detection needed - PTT only
        
        print(f"📝 You: {text}")
        
        # Check for session file requests
        lower = text.lower()
        match = re.search(r'session\s*(\d+)', lower)
        if match:
            num = int(match.group(1))
            content = read_campaign_file(f"session-{num:02d}.md")
            if content:
                text += f"\n\n[Session {num} content loaded. Summarize key info verbally.]"
        
        # Check for dice rolls
        dice_match = re.search(r'(\d*d\d+[^\s]*)', text.lower())
        if dice_match and ('roll' in lower or 'rolled' in lower):
            result = roll_dice(dice_match.group(1))
            if result:
                roll_text = format_roll(result)
                text += f"\n\n[Roll result: {roll_text}]"
        
        # Check for damage/heal commands
        damage_match = re.search(r'(?:take|took)\s*(\d+)\s*damage', lower)
        if damage_match and character.name:
            dmg = int(damage_match.group(1))
            dead = character.take_damage(dmg)
            character.save()
            text += f"\n\n[Character took {dmg} damage. HP: {character.hp}/{character.max_hp}{' - UNCONSCIOUS!' if dead else ''}]"
        
        heal_match = re.search(r'(?:heal|healed)\s*(\d+)', lower)
        if heal_match and character.name:
            amt = int(heal_match.group(1))
            character.heal(amt)
            character.save()
            text += f"\n\n[Character healed {amt}. HP: {character.hp}/{character.max_hp}]"
        
        # Add to history
        history.append({"role": "user", "content": text})
        if len(history) > 21:
            history[:] = [history[0]] + history[-20:]
        
        print("🤔 Thinking...")
        
        # Get response
        try:
            data = json.dumps({"model": MODEL, "messages": history, "max_tokens": 400, "temperature": 0.7}).encode()
            req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())
                reply = result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"❌ API error: {e}")
            history.pop()
            continue
        
        # Strip thinking tags
        reply_clean = re.sub(r'<think>.*？', '', reply, flags=re.DOTALL).strip()
        if '</think>' in reply:
            reply_clean = reply.split('</think>')[-1].strip()
        if reply_clean.startswith('<think>'):
            reply_clean = ''
        
        if not reply_clean:
            print("⚠️  Empty response, waiting before retry...")
            history.pop()
            time.sleep(5)
            continue
        
        print(f"💬 DM: {reply_clean}")
        
        # Parse and send VTT commands, strip them from spoken text
        speakable = parse_and_send_vtt_commands(reply_clean)
        
        history.append({"role": "assistant", "content": reply_clean})
        
        # Speak - wait for full playback + buffer
        text_to_speech(speakable, VOICES["narrator"], loop)
        playback_time = estimate_playback(speakable)
        print(f"   🔊 Speaking ({playback_time:.0f}s)...")
        time.sleep(playback_time + 3)  # extra buffer to prevent echo
        cooldown_until = time.time() + 2
        print("✅\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🔇 Voice DM stopped.")
