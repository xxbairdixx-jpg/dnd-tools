# VTT Feature Roadmap

> **Architecture:** See `ARCHITECTURE.md` for official design.
> **Stack:** Python backend (engine + modules) + JavaScript frontend (renderer only)

---

## 🏗️ Phase 0 — Refactor to Python Architecture

- [ ] Create `vtt/` folder structure (engine/, modules/, web/, data/)
- [ ] Build `engine/core.py` — module loader, bootstrap
- [ ] Build `engine/state.py` — global game state management
- [ ] Build `engine/api.py` — Flask/FastAPI REST + WebSocket
- [ ] Implement event system (pub/sub between modules)
- [ ] Port existing Node.js features to Python modules
- [ ] Keep current JS frontend as renderer (refactor later)

## 🎯 Priority 1 — Core VTT Features (Get Working)

### Maps
- [ ] Map background image upload/URL
- [ ] Multiple maps (switch between them)
- [ ] Grid overlay (square/hex toggle)
- [ ] Grid size configuration (default 5ft squares)
- [ ] Map zoom & pan (mouse wheel + drag)
- [ ] Map layers (background, objects, tokens, fog, GM overlay)

### Token System
- [ ] Token images (upload PNG with transparency)
- [ ] Token drag & drop on grid
- [ ] Token snap-to-grid
- [ ] Token properties (name, HP, AC, size)
- [ ] Token size (small, medium, large, huge, gargantuan)
- [ ] Token rotation
- [ ] Token visibility (hidden from players)
- [ ] Token states/conditions (colored overlays: bloodied, stunned, etc.)
- [ ] Token bars (HP bar, resource bars above token)
- [ ] Token labels (name, number, custom)
- [ ] Token initiative tracker

### Object Placement
- [ ] Furniture objects (tables, chairs, beds, bookshelves)
- [ ] Dungeon objects (chests, barrels, crates, doors)
- [ ] Nature objects (trees, rocks, bushes, water)
- [ ] Walls & barriers
- [ ] Object drag & drop from asset library
- [ ] Object rotation & scaling
- [ ] Object layer ordering

### Fog of War
- [ ] GM reveals/hides areas
- [ ] Player-specific fog (each player sees different areas)
- [ ] Fog brush tool (paint to reveal)
- [ ] Fog rectangle tool
- [ ] Auto-reveal on token movement
- [ ] Fog persistence between sessions

### Vision & Lighting
- [ ] Token sight ranges (darkvision 60ft, etc.)
- [ ] Light sources (torches, lanterns, spells)
- [ ] Light radius & color
- [ ] Dynamic lighting (walls block light)
- [ ] Day/night cycle toggle
- [ ] Vision modes (normal, darkvision, blindsight, truesight)

---

## 🎯 Priority 2 — Gameplay Features

### Dice System
- [x] Basic dice rolling (d4-d100)
- [ ] Dice expressions (2d6+3, 4d6kh3, etc.)
- [ ] Roll macros (save frequently used rolls)
- [ ] Roll history
- [ ] Private rolls (GM only)
- [ ] Dice tray (visual dice rolling)

### Initiative Tracker
- [ ] Initiative order list
- [ ] Add/remove from initiative
- [ ] Sort by initiative score
- [ ] Round counter
- [ ] Turn indicator
- [ ] Hold/delay turn
- [ ] Link tokens to initiative

### Character Sheets
- [ ] Basic stat block (name, HP, AC, speed)
- [ ] Ability scores (STR, DEX, CON, INT, WIS, CHA)
- [ ] Saving throws
- [ ] Skills list
- [ ] Spell slots tracker
- [ ] Inventory
- [ ] Notes field

### Chat & Communication
- [x] Text chat
- [ ] Chat commands (/roll, /w, /emote)
- [ ] Whisper (private messages)
- [ ] Emotes
- [ ] GM announcements
- [ ] Chat formatting (bold, italic)

### Measurement Tools
- [ ] Ruler (measure distance)
- [ ] Line tool
- [ ] Circle/area template
- [ ] Cone template
- [ ] Square template
- [ ] Movement path visualization
- [ ] Range indicators

---

## 🎯 Priority 3 — Advanced Features

### Map Drawing
- [ ] Freehand drawing tool
- [ ] Line/shape tools
- [ ] Paint tool (textured brushes)
- [ ] Eraser
- [ ] Fill tool
- [ ] Undo/redo

### Walls & Doors
- [ ] Wall placement tool
- [ ] Wall types (stone, wood, invisible)
- [ ] Door placement (open, closed, locked, secret)
- [ ] Door toggle (open/close)
- [ ] Walls block movement
- [ ] Walls block vision/light

### Traps & Hazards
- [ ] Trap markers
- [ ] Hidden trap toggle (GM sees, players don't)
- [ ] Hazard zones (fire, acid, difficult terrain)
- [ ] Trigger areas

### Sound & Music
- [ ] Ambient sound zones
- [ ] Music playlist
- [ ] Sound triggers (enter area → play sound)
- [ ] Volume control per zone

### Campaign Management
- [ ] Save/load campaign
- [ ] Multiple campaigns
- [ ] Session notes
- [ ] Map library
- [ ] Token library
- [ ] Export/import assets

### GM Tools
- [ ] GM screen (hidden info panel)
- [ ] GM notes per map
- [ ] Hidden rolls
- [ ] Player view toggle (see what players see)
- [ ] Teleport tokens between maps
- [ ] Copy/paste tokens
- [ ] Select multiple tokens

### Player Features (Local/LAN)
- [ ] Player token ownership (players can only move their tokens)
- [ ] Player journal (shared notes)
- [ ] Player handouts (images, text)
- [ ] Room code for LAN players to connect
- [ ] GM controls what players see vs hidden

---

## 🎯 Priority 4 — AI/GM Agent Integration

### Agent API Endpoints
- [x] POST /api/token/add
- [x] POST /api/token/move
- [x] POST /api/token/remove
- [x] POST /api/roll
- [x] POST /api/chat
- [x] GET /api/state
- [ ] POST /api/initiative/add
- [ ] POST /api/initiative/next
- [ ] POST /api/fog/reveal
- [ ] POST /api/fog/hide
- [ ] POST /api/map/switch
- [ ] POST /api/map/create
- [ ] POST /api/token/update (HP, conditions, etc.)
- [ ] POST /api/light/add
- [ ] POST /api/wall/add
- [ ] POST /api/door/toggle
- [ ] GET /api/vision/check (can token X see token Y?)
- [ ] POST /api/narrate (GM narration with TTS)

### Voice Integration
- [ ] TTS for GM narration (edge-tts)
- [ ] NPC voice assignment
- [ ] Auto-narrate on events
- [ ] Voice chat (WebRTC)

### AI Features
- [ ] Auto-generate maps from description
- [ ] Auto-place tokens from encounter description
- [ ] Smart fog reveal (based on token movement)
- [ ] Combat narration
- [ ] Loot generation
- [ ] NPC dialogue generation

---

## 📋 PDF Extraction Tasks (for Nemotron)

- [ ] Extract Monster Manual → parse all stat blocks → update monsters-complete.md
- [ ] Extract Player's Handbook → parse all spells → update spells-complete.md
- [ ] Extract DMG → parse magic items → update magic-items.md
- [ ] Extract DMG → parse treasure tables → create treasure-tables.md
- [ ] Extract Sword Coast → parse additional content
- [ ] Cross-reference SRD vs full books → identify missing content

---

## 🎯 Priority 5 — Quality of Life & Polish

### UX
- [ ] Auto-save (never lose work)
- [ ] Keyboard shortcuts (N=next turn, R=roll, T=add token, Del=delete)
- [ ] Undo/redo for map edits
- [ ] Copy/paste tokens and objects
- [ ] Multi-select tokens (shift+click or drag box)
- [ ] Token pathfinding (auto-route around walls)
- [ ] Map bookmarks/pins (click pin → see location notes)

### Visual Effects
- [ ] Token animations (smooth movement between cells)
- [ ] Weather overlays (rain, snow, fog particles)
- [ ] Day/night visual filter
- [ ] Blood splatter / damage effects on tokens
- [ ] Spell effect templates (fireball circle, cone, line)

### Map Building Tools
- [ ] Map stamps (quick-place repeated objects like trees, pillars)
- [ ] Symmetry tool (draw half, mirror it)
- [ ] Texture brushes (paint floors, walls, water)
- [ ] Pre-built room templates (tavern, dungeon room, throne room)

### In-App Tools
- [ ] Built-in rules reference (pull from your SRD files)
- [ ] Encounter builder (pick monsters from list, auto-calc XP/CR)
- [ ] Loot generator (random treasure by CR)
- [ ] In-game calendar / time tracker
- [ ] Party resource tracker (rations, torches, arrows, gold)
- [ ] PDF viewer (read sourcebooks while playing)

---

## 📦 Asset Downloads

- [ ] Download 2-Minute Tabletop starter pack
- [ ] Download Forgotten Adventures free tokens
- [ ] Download Tom Cartos free objects
- [ ] Create default token set (colored circles with initials)
- [ ] Create default map backgrounds (dungeon, forest, tavern)

---

*Last updated: 2026-03-18*
