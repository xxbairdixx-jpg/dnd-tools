"""
Combat Module

Initiative tracking, turns, damage, healing, conditions.
Emits: combat_started, combat_ended, turn_started, turn_ended, round_started,
       damage_applied, heal_applied, condition_added, condition_removed
Listens to: token_removed (remove from initiative)
"""

from typing import Any, Dict, List

_state = None
_event_bus = None

# D&D 5e conditions
VALID_CONDITIONS = {
    "blinded", "charmed", "deafened", "frightened", "grappled",
    "incapacitated", "invisible", "paralyzed", "petrified", "poisoned",
    "prone", "restrained", "stunned", "unconscious",
}


def init(state, event_bus):
    """Initialize the module."""
    global _state, _event_bus
    _state = state
    _event_bus = event_bus
    # Listen for token removal to clean up initiative
    event_bus.subscribe("token_removed", _on_token_removed)


def _on_token_removed(event):
    """Remove token from initiative when removed."""
    token_id = event["data"]["token"]["id"]
    if token_id in _state.initiative:
        _state.initiative.remove(token_id)
        if _state.turn == token_id:
            _next_turn_internal()


def get_api() -> Dict[str, Any]:
    """Return API functions."""
    return {
        "start_combat": start_combat,
        "end_combat": end_combat,
        "end_turn": end_turn,
        "set_initiative": set_initiative,
        "apply_damage": apply_damage,
        "apply_heal": apply_heal,
        "add_condition": add_condition,
        "remove_condition": remove_condition,
        "set_concentration": set_concentration,
        "break_concentration": break_concentration,
        "death_save": death_save,
        "reset_death_saves": reset_death_saves,
        "short_rest": short_rest,
        "long_rest": long_rest,
        "roll_initiative": roll_initiative,
    }


def start_combat(token_ids: List[str] = None) -> Dict[str, Any]:
    """Start combat with the given tokens."""
    if token_ids is None:
        token_ids = list(_state.tokens.keys())

    if len(token_ids) < 2:
        return {"error": "Need at least 2 tokens for combat"}

    _state.initiative = token_ids
    _state.combat_active = True
    _state.round = 1
    _state.turn = token_ids[0]

    result = {
        "initiative": _state.initiative,
        "turn": _state.turn,
        "round": _state.round,
    }

    if _event_bus:
        _event_bus.emit("combat_started", result, source="combat_module")
        _event_bus.emit("turn_started", {"token_id": _state.turn, "round": _state.round}, source="combat_module")

    return result


def end_combat() -> Dict[str, Any]:
    """End combat."""
    _state.combat_active = False
    _state.initiative = []
    _state.turn = None
    _state.round = 0

    if _event_bus:
        _event_bus.emit("combat_ended", {}, source="combat_module")

    return {"combat_active": False}


def end_turn() -> Dict[str, Any]:
    """End the current turn and advance to the next."""
    if not _state.combat_active:
        return {"error": "No active combat"}

    old_turn = _state.turn
    _next_turn_internal()

    result = {
        "previous_turn": old_turn,
        "current_turn": _state.turn,
        "round": _state.round,
    }

    if _event_bus:
        _event_bus.emit("turn_ended", {"token_id": old_turn}, source="combat_module")
        _event_bus.emit("turn_started", {"token_id": _state.turn, "round": _state.round}, source="combat_module")

    return result


def _next_turn_internal():
    """Advance to the next turn (internal, no events)."""
    if not _state.initiative:
        return

    current_idx = _state.initiative.index(_state.turn) if _state.turn in _state.initiative else -1
    next_idx = (current_idx + 1) % len(_state.initiative)

    if next_idx == 0 and current_idx >= 0:
        _state.round += 1
        if _event_bus:
            _event_bus.emit("round_started", {"round": _state.round}, source="combat_module")

    _state.turn = _state.initiative[next_idx]


def set_initiative(token_id: str, score: int) -> Dict[str, Any]:
    """Set a token's initiative score and re-sort."""
    token = _state.get_token(token_id)
    if not token:
        return {"error": f"Token not found: {token_id}"}

    token["initiative"] = score

    # Sort initiative by score (descending)
    _state.initiative.sort(key=lambda tid: _state.tokens.get(tid, {}).get("initiative", 0), reverse=True)

    return {"token_id": token_id, "initiative": score, "order": _state.initiative}


def apply_damage(token_id: str, amount: int) -> Dict[str, Any]:
    """Apply damage to a token."""
    token = _state.get_token(token_id)
    if not token:
        return {"error": f"Token not found: {token_id}"}

    token["hp"] = max(0, token["hp"] - amount)

    result = {
        "token_id": token_id,
        "damage": amount,
        "hp": token["hp"],
        "max_hp": token["max_hp"],
        "unconscious": token["hp"] <= 0,
    }

    if _event_bus:
        _event_bus.emit("damage_applied", result, source="combat_module")

    return result


def apply_heal(token_id: str, amount: int) -> Dict[str, Any]:
    """Apply healing to a token."""
    token = _state.get_token(token_id)
    if not token:
        return {"error": f"Token not found: {token_id}"}

    token["hp"] = min(token["max_hp"], token["hp"] + amount)

    result = {
        "token_id": token_id,
        "healing": amount,
        "hp": token["hp"],
        "max_hp": token["max_hp"],
    }

    if _event_bus:
        _event_bus.emit("heal_applied", result, source="combat_module")

    return result


def add_condition(token_id: str, condition: str) -> Dict[str, Any]:
    """Add a condition to a token."""
    token = _state.get_token(token_id)
    if not token:
        return {"error": f"Token not found: {token_id}"}

    condition = condition.lower()
    if condition not in VALID_CONDITIONS:
        return {"error": f"Invalid condition: {condition}"}

    if "conditions" not in token:
        token["conditions"] = []

    if condition not in token["conditions"]:
        token["conditions"].append(condition)

    if _event_bus:
        _event_bus.emit("condition_added", {"token_id": token_id, "condition": condition}, source="combat_module")

    return {"token_id": token_id, "conditions": token["conditions"]}


def remove_condition(token_id: str, condition: str) -> Dict[str, Any]:
    """Remove a condition from a token."""
    token = _state.get_token(token_id)
    if not token:
        return {"error": f"Token not found: {token_id}"}

    condition = condition.lower()
    if "conditions" in token and condition in token["conditions"]:
        token["conditions"].remove(condition)

    if _event_bus:
        _event_bus.emit("condition_removed", {"token_id": token_id, "condition": condition}, source="combat_module")

    return {"token_id": token_id, "conditions": token.get("conditions", [])}


def set_concentration(token_id: str, spell: str = "", dc: int = 10) -> Dict[str, Any]:
    """Mark a token as concentrating on a spell."""
    token = _state.get_token(token_id)
    if not token:
        return {"error": f"Token not found: {token_id}"}
    token["concentration"] = {"spell": spell, "dc": dc}
    return {"token_id": token_id, "concentration": token["concentration"]}


def break_concentration(token_id: str) -> Dict[str, Any]:
    """Remove concentration from a token."""
    token = _state.get_token(token_id)
    if not token:
        return {"error": f"Token not found: {token_id}"}
    old = token.pop("concentration", None)
    return {"token_id": token_id, "was_concentrating": old}


def death_save(token_id: str, success: bool = True) -> Dict[str, Any]:
    """Record a death saving throw."""
    token = _state.get_token(token_id)
    if not token:
        return {"error": f"Token not found: {token_id}"}
    if "death_saves" not in token:
        token["death_saves"] = {"successes": 0, "failures": 0}
    if success:
        token["death_saves"]["successes"] = min(3, token["death_saves"]["successes"] + 1)
    else:
        token["death_saves"]["failures"] = min(3, token["death_saves"]["failures"] + 1)
    result = {
        "token_id": token_id,
        "successes": token["death_saves"]["successes"],
        "failures": token["death_saves"]["failures"],
        "stabilized": token["death_saves"]["successes"] >= 3,
        "dead": token["death_saves"]["failures"] >= 3,
    }
    if _event_bus:
        _event_bus.emit("death_save", result, source="combat_module")
    return result


def reset_death_saves(token_id: str) -> Dict[str, Any]:
    """Reset death saves (on heal or stabilize)."""
    token = _state.get_token(token_id)
    if not token:
        return {"error": f"Token not found: {token_id}"}
    token["death_saves"] = {"successes": 0, "failures": 0}
    return {"token_id": token_id, "death_saves": token["death_saves"]}


def short_rest(token_ids: List[str] = None) -> Dict[str, Any]:
    """Apply short rest benefits (spend Hit Dice to heal)."""
    if token_ids is None:
        token_ids = list(_state.tokens.keys())
    results = {}
    for tid in token_ids:
        token = _state.get_token(tid)
        if token:
            # Reset short rest abilities (simplified)
            if "conditions" in token:
                token["conditions"] = [c for c in token["conditions"] if c not in {"exhaustion"}]
            results[tid] = {"name": token["name"], "hp": token["hp"]}
    return {"rest": "short", "tokens": results}


def long_rest(token_ids: List[str] = None) -> Dict[str, Any]:
    """Apply long rest benefits (full heal, reset all)."""
    if token_ids is None:
        token_ids = list(_state.tokens.keys())
    results = {}
    for tid in token_ids:
        token = _state.get_token(tid)
        if token:
            token["hp"] = token.get("max_hp", token["hp"])
            token["conditions"] = []
            token["death_saves"] = {"successes": 0, "failures": 0}
            token.pop("concentration", None)
            results[tid] = {"name": token["name"], "hp": token["hp"]}
    if _event_bus:
        _event_bus.emit("long_rest", {"tokens": results}, source="combat_module")
    return {"rest": "long", "tokens": results}


def roll_initiative(token_ids: List[str] = None) -> Dict[str, Any]:
    """Roll initiative for all tokens and sort."""
    import random
    if token_ids is None:
        token_ids = list(_state.tokens.keys())
    rolls = {}
    for tid in token_ids:
        token = _state.get_token(tid)
        if token:
            roll = random.randint(1, 20)
            dex_mod = token.get("dex_mod", 0)
            total = roll + dex_mod
            token["initiative"] = total
            rolls[tid] = {"name": token["name"], "roll": roll, "modifier": dex_mod, "total": total}
    # Sort initiative
    _state.initiative = sorted(token_ids, key=lambda tid: _state.tokens.get(tid, {}).get("initiative", 0), reverse=True)
    if _state.initiative:
        _state.turn = _state.initiative[0]
        _state.combat_active = True
        _state.round = 1
    if _event_bus:
        _event_bus.emit("combat_started", {"initiative": _state.initiative, "turn": _state.turn, "round": _state.round, "rolls": rolls}, source="combat_module")
    return {"initiative": _state.initiative, "rolls": rolls, "turn": _state.turn}
