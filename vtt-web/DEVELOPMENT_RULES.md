# VTT Development Rules

## Planning Requirement

Before implementing any feature, produce a development plan:

- **Goal** — what does this feature accomplish?
- **Modules affected** — which modules need changes?
- **New files required** — what gets created?
- **API changes** — new endpoints or modified signatures?
- **Tests required** — how do we verify it works?

Only after the plan is complete should implementation begin.

---

## Task Management

Maintain a persistent task queue in `TASKS.md`.

Each task contains:
- **Task ID** — unique identifier (e.g., ASSET-001, ENGINE-001)
- **Description** — what needs to be done
- **Status** — planned / in_progress / complete
- **Dependencies** — which tasks must complete first

Tasks must be completed in logical order.
Always update the task queue after completing a task.

---

## Error Handling

When an error occurs:
1. Capture the error output
2. Analyze the cause
3. Propose a fix
4. Apply the fix
5. Rerun the test

Never abandon a feature due to an error.
Always attempt to repair the implementation.

---

## Campaign Memory System

Maintain persistent world memory in `data/campaigns/`.

Store:
- NPC identities (name, race, class, location, disposition)
- Locations (name, description, connected areas)
- Factions (name, alignment, goals, relationships)
- Quests (name, status, objectives, rewards)
- Major world events (date, description, impact)
- Player decisions (what, when, consequences)

Memory must persist between sessions.
Important events should be summarized as structured records.
Agents must consult world memory before generating story events.

---

## Module Documentation

Each module must contain a docstring explaining:
- Purpose of the module
- Available API functions
- Events emitted
- Events listened to

Documentation must be updated whenever the module changes.

---

## Automated Testing

Create simulation scripts that test gameplay systems:
- Combat simulations (run 1000 fights, check balance)
- Dice probability tests (verify distributions)
- Initiative order tests (verify turn order)

Run tests after modifying gameplay modules.

---

*Bairdi's development rules — 2026-03-18*
