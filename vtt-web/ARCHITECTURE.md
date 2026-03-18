# VTT Architecture — Official Design Document

## Gameplay Flow

When a player performs an action:

1. **Rules Agent** resolves mechanics and dice rolls
2. **World Agent** updates persistent campaign state
3. **Story Agent** generates narration
4. **System Agent** updates the VTT

---

## Engine + Modules Architecture

The VTT follows an **engine-plus-modules** architecture.

### Core Engine (minimal, no game logic)

Responsibilities:
- State management
- Event dispatch
- Module loading
- API exposure

### Modules (implement specific game systems)

| Module | Responsibility |
|--------|---------------|
| `map_module` | Grid, backgrounds, fog, vision |
| `token_module` | Token CRUD, movement, properties |
| `combat_module` | Initiative, turns, conditions |
| `dice_module` | Dice expressions, roll history |

**Future modules:** spells, factions, weather, traps, loot, calendar

---

## Folder Structure

```
vtt/
├── engine/
│   ├── core.py          # Engine bootstrap, module loader
│   ├── state.py         # Global game state management
│   └── api.py           # REST/WebSocket API layer
│
├── modules/
│   ├── map_module.py    # Map grid, backgrounds, fog
│   ├── token_module.py  # Token CRUD, movement, properties
│   ├── combat_module.py # Initiative, turns, conditions
│   └── dice_module.py   # Dice rolling, expressions
│
├── web/
│   ├── index.html       # UI shell
│   ├── renderer.js      # Canvas rendering (no logic)
│   └── ui.js            # UI event handlers (no logic)
│
└── data/
    ├── campaigns/       # Saved campaign state
    ├── maps/            # Map images & configs
    └── npcs/            # NPC data & stat blocks
```

---

## Global Game State

Single authoritative state object:

```json
{
  "map_size": [60, 60],
  "tokens": [
    {"id": "fighter", "x": 3, "y": 5, "hp": 22, "ac": 18, "name": "Thorin"},
    {"id": "goblin_1", "x": 5, "y": 6, "hp": 7, "ac": 15, "name": "Goblin"}
  ],
  "initiative": ["fighter", "goblin_1"],
  "turn": "fighter",
  "round": 1,
  "fog": [],
  "map_background": null,
  "lights": [],
  "walls": []
}
```

The state object is the **authoritative representation** of the game world.

---

## Event System

Modules communicate through events (no direct dependencies).

### Event Types

| Event | Trigger |
|-------|---------|
| `token_spawned` | New token added |
| `token_moved` | Token position changed |
| `token_removed` | Token deleted |
| `damage_applied` | HP reduced |
| `heal_applied` | HP increased |
| `combat_started` | Initiative rolled |
| `turn_ended` | Current turn passed |
| `round_started` | New round begins |
| `dice_rolled` | Dice expression resolved |
| `fog_revealed` | Area uncovered |
| `condition_added` | Status effect applied |
| `condition_removed` | Status effect cleared |

The engine dispatches events when state changes occur.
Modules subscribe to events and update their systems.

---

## VTT Control API

Commands for agent (AI GM) control:

```python
# Token management
spawn_token(name, token_type, x, y, **properties)
move_token(token_id, x, y)
remove_token(token_id)
update_token(token_id, **properties)

# Combat
start_combat()
end_turn()
set_initiative(token_id, score)
apply_damage(token_id, amount)
apply_heal(token_id, amount)
add_condition(token_id, condition)
remove_condition(token_id, condition)

# Dice
roll_dice(expression)  # "2d6+3", "1d20", "4d6kh3"

# Map
set_map_background(url)
reveal_fog(x, y, radius)
hide_fog(x, y, radius)
add_light(x, y, radius, color)
add_wall(x1, y1, x2, y2)

# State
get_game_state()
save_campaign(name)
load_campaign(name)
```

The AI Dungeon Master interacts with the game **only through these commands**.

---

## User Interface

The web interface is a **dumb renderer** — no game logic.

### Displays:
- Grid map (canvas)
- Tokens (rendered from state)
- Initiative tracker (read from state)
- Combat log (event history)

### Rules:
- Game logic **never** exists in the interface layer
- All logic lives in the engine or modules
- UI sends commands to API → API updates state → UI re-renders

---

## Code Generation Rules

- **Python** for backend systems (engine, modules, API)
- **JavaScript + HTML** for web interface (renderer only)
- Keep files **small and modular**
- Avoid complex dependencies between modules
- **Document APIs clearly**

---

## Development Process

Always follow this loop:

1. **Plan** the feature
2. **Generate** code
3. **Execute** and test the module
4. **Analyze** errors
5. **Fix** issues
6. **Integrate** into the system

---

## System Completion Criteria

When fully operational, the system should be capable of:

- Running tabletop RPG campaigns
- Generating narrative scenes
- Tracking initiative and combat
- Controlling a virtual tabletop map
- Maintaining world lore across sessions
- Accepting voice commands
- Narrating events through speech output
- Expanding itself with new gameplay modules

**Build incrementally. Verify each subsystem before expanding.**

---

*Architecture by Bairdi — 2026-03-18*
