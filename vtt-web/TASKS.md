# VTT Task Queue

> Rules: See `DEVELOPMENT_RULES.md`
> Architecture: See `ARCHITECTURE.md`

---

## 🎨 ASSETS — Collect VTT Assets

### ASSET-001: Download 2-Minute Tabletop Starter Pack
- **Status:** complete ✅
- **Result:** 6 maps, 71 assets, 50 tokens downloaded to assets/2minutetabletop/
- **Dependencies:** none
- **Agent:** Nemotron
- **Instructions:**
  1. Fetch https://2minutetabletop.com
  2. Find the "First Time on 2MT?" section
  3. Download these 5 packs:
     - The Town Center city maps
     - The Forest Camp forest maps
     - The Thermal Mines dungeon maps
     - 71 textures & map assets
     - 50 hero & monster tokens
  4. Save to `vtt-web/assets/2minutetabletop/`
  5. Unzip if needed
  6. List all downloaded files in completion report

### ASSET-002: Download Forgotten Adventures Free Tokens
- **Status:** planned
- **Dependencies:** none
- **Agent:** Nemotron
- **Instructions:**
  1. Fetch https://www.forgotten-adventures.net
  2. Navigate to free downloads section
  3. Download any free token packs available
  4. Save to `vtt-web/assets/forgotten-adventures/`
  5. List all downloaded files

### ASSET-003: Download Tom Cartos Free Objects
- **Status:** planned
- **Dependencies:** none
- **Agent:** Nemotron
- **Instructions:**
  1. Fetch https://www.tomcartos.com
  2. Find freebies section
  3. Download free object/prop packs
  4. Save to `vtt-web/assets/tomcartos/`
  5. List all downloaded files

### ASSET-004: Create Default Token Set
- **Status:** complete ✅
- **Result:** 8 colored tokens (A-H) with manifest at assets/tokens/default/
- **Dependencies:** none
- **Agent:** Sentinel
- **Instructions:**
  1. Create colored circle tokens (PNG, 200x200px, transparent bg)
  2. Colors: red, blue, green, yellow, purple, orange, white, black
  3. Each token has a centered letter (A-H)
  4. Save to `vtt-web/assets/tokens/default/`
  5. Create a token manifest JSON listing all tokens

### ASSET-005: Create Default Map Backgrounds
- **Status:** complete ✅
- **Result:** 4 maps (dungeon, forest, tavern, cave) with manifest at assets/maps/default/
- **Dependencies:** none
- **Agent:** Sentinel
- **Instructions:**
  1. Create simple grid backgrounds (1920x1080 or 1200x800)
  2. Themes: dungeon stone, forest grass, tavern wood, cave rock
  3. Include grid overlay (40px cells)
  4. Save to `vtt-web/assets/maps/default/`
  5. Create a map manifest JSON

---

## 🔧 ENGINE — Build Python Backend

### ENGINE-001: Create Folder Structure
- **Status:** planned
- **Dependencies:** none
- **Agent:** Sentinel
- **Instructions:**
  1. Create `vtt/` with subdirs: engine/, modules/, web/, data/
  2. Create `data/campaigns/`, `data/maps/`, `data/npcs/`
  3. Create `__init__.py` in each Python dir
  4. Create placeholder files: core.py, state.py, api.py

### ENGINE-002: Build State Manager
- **Status:** planned
- **Dependencies:** ENGINE-001
- **Agent:** Llama Ultra
- **Instructions:**
  1. Create `engine/state.py`
  2. Implement GameState class with:
     - `tokens` dict (id → token data)
     - `initiative` list
     - `turn` string (current token id)
     - `round` int
     - `fog` list
     - `map_size` tuple
     - `map_background` string
     - `lights` list
     - `walls` list
  3. Methods: `to_dict()`, `from_dict()`, `save(filename)`, `load(filename)`
  4. All state changes go through the state object

### ENGINE-003: Build Event System
- **Status:** planned
- **Dependencies:** ENGINE-002
- **Agent:** Llama Ultra
- **Instructions:**
  1. Create `engine/events.py`
  2. Implement EventBus class with:
     - `subscribe(event_type, callback)` — register listener
     - `emit(event_type, data)` — dispatch event
     - `unsubscribe(event_type, callback)` — remove listener
  3. Event types: token_spawned, token_moved, token_removed,
     damage_applied, heal_applied, combat_started, turn_ended,
     round_started, dice_rolled, fog_revealed, condition_added
  4. Events carry timestamp and source module name

### ENGINE-004: Build Module Loader
- **Status:** planned
- **Dependencies:** ENGINE-003
- **Agent:** Llama Ultra
- **Instructions:**
  1. Create `engine/core.py`
  2. Implement ModuleLoader that:
     - Scans `modules/` directory
     - Loads each module (import + init)
     - Passes state and event_bus to each module
     - Collects API functions from all modules
  3. Each module must have: `init(state, event_bus)` and `get_api()` functions

### ENGINE-005: Build API Layer
- **Status:** planned
- **Dependencies:** ENGINE-004
- **Agent:** Llama Ultra
- **Instructions:**
  1. Create `engine/api.py` using Flask
  2. Expose all module API functions as REST endpoints
  3. WebSocket endpoint for real-time state updates
  4. Endpoints match ARCHITECTURE.md API spec
  5. Serve static files from `web/`

---

## 🧩 MODULES — Game System Modules

### MODULE-001: Dice Module
- **Status:** planned
- **Dependencies:** ENGINE-003
- **Agent:** Llama Ultra
- **Instructions:**
  1. Create `modules/dice_module.py`
  2. Parse dice expressions: NdM, NdM+X, NdM-X, NdMkhN, NdMklN
  3. Roll and return: {expression, rolls, modifier, total}
  4. Emit `dice_rolled` event
  5. API: `roll_dice(expression)`
  6. Test: verify 1000 rolls of 1d20 produce uniform distribution

### MODULE-002: Token Module
- **Status:** planned
- **Dependencies:** ENGINE-002
- **Agent:** Llama Ultra
- **Instructions:**
  1. Create `modules/token_module.py`
  2. API: spawn_token, move_token, remove_token, update_token
  3. Emit events: token_spawned, token_moved, token_removed
  4. Validate: position within map bounds, no duplicate IDs
  5. Token properties: id, name, x, y, hp, max_hp, ac, size, color, image, conditions

### MODULE-003: Map Module
- **Status:** planned
- **Dependencies:** ENGINE-002
- **Agent:** Llama Ultra
- **Instructions:**
  1. Create `modules/map_module.py`
  2. API: set_background, reveal_fog, hide_fog, add_light, add_wall
  3. Grid management: set_size, get_cell
  4. Emit events: fog_revealed, light_added, wall_added
  5. Vision calculation: which tokens can see which cells

### MODULE-004: Combat Module
- **Status:** planned
- **Dependencies:** MODULE-001, MODULE-002
- **Agent:** Llama Ultra
- **Instructions:**
  1. Create `modules/combat_module.py`
  2. API: start_combat, end_turn, set_initiative, apply_damage, apply_heal, add_condition, remove_condition
  3. Emit events: combat_started, turn_ended, round_started, damage_applied, condition_added
  4. Initiative tracking with tie-breaking
  5. Condition list: blinded, charmed, deafened, frightened, grappled, incapacitated, invisible, paralyzed, petrified, poisoned, prone, restrained, stunned, unconscious

---

## 📄 PDF EXTRACTION — Parse Sourcebooks

### PDF-001: Extract Monster Manual
- **Status:** complete ✅
- **Result:** 230 unique monsters extracted to references/monsters-full.md
- **Dependencies:** none
- **Agent:** Nemotron
- **Instructions:**
  1. Run: `pdftotext "dnd-pdfs/0 Core books/D&D 5E - Monster Manual.pdf" /tmp/mm.txt`
  2. Parse stat blocks: name, type, size, AC, HP, speed, STR, DEX, CON, INT, WIS, CHA, CR
  3. Save to `references/monsters-full.md` (overwrite existing SRD-only version)
  4. Count total monsters extracted
  5. Compare with SRD (334) to show what was added

### PDF-002: Extract Player's Handbook Spells
- **Status:** complete ✅
- **Result:** 225 spells extracted to references/spells-full.md
- **Dependencies:** none
- **Agent:** Nemotron
- **Instructions:**
  1. Run: `pdftotext "dnd-pdfs/0 Core books/D&D 5E - Player's Handbook.pdf" /tmp/phb.txt`
  2. Parse spells: name, level, school, casting time, range, components, duration, description
  3. Save to `references/spells-full.md` (overwrite existing SRD-only version)
  4. Count total spells extracted
  5. Compare with SRD (319) to show what was added

### PDF-003: Extract DMG Magic Items
- **Status:** planned
- **Dependencies:** none
- **Agent:** Nemotron
- **Instructions:**
  1. Run: `pdftotext "dnd-pdfs/0 Core books/D&D 5E - Dungeon Master's Guide.pdf" /tmp/dmg.txt`
  2. Parse magic items: name, type, rarity, attunement, description
  3. Save to `references/magic-items-full.md`
  4. Count total items extracted

---

## 🧪 TESTING

### TEST-001: Dice Probability Test
- **Status:** planned
- **Dependencies:** MODULE-001
- **Agent:** Llama Ultra
- **Instructions:**
  1. Roll 10,000 d20s
  2. Verify each face appears ~500 times (±10%)
  3. Roll 10,000 2d6+3
  4. Verify distribution peaks at 10
  5. Report pass/fail with statistics

### TEST-002: Combat Simulation
- **Status:** planned
- **Dependencies:** MODULE-004
- **Agent:** Llama Ultra
- **Instructions:**
  1. Create Fighter (HP 28, AC 18, +5 attack, 1d8+3 damage) vs Goblin (HP 7, AC 15, +4 attack, 1d6+2 damage)
  2. Run 1000 simulated combats
  3. Track: win rate, average rounds, average damage dealt
  4. Verify combat completes (no infinite loops)
  5. Report statistics

---

*Last updated: 2026-03-18*
