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
