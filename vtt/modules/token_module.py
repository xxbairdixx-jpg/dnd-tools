"""
Token Module

Token CRUD, movement, properties.
Emits: token_spawned, token_moved, token_removed, token_updated
Listens to: (none)
"""

from typing import Any, Dict, Optional

_state = None
_event_bus = None


def init(state, event_bus):
    """Initialize the module."""
    global _state, _event_bus
    _state = state
    _event_bus = event_bus


def get_api() -> Dict[str, Any]:
    """Return API functions."""
    return {
        "spawn_token": spawn_token,
        "move_token": move_token,
        "remove_token": remove_token,
        "update_token": update_token,
    }


def spawn_token(
    name: str = "Token",
    token_type: str = "npc",
    x: int = 0,
    y: int = 0,
    hp: int = 10,
    max_hp: int = 10,
    ac: int = 10,
    size: str = "medium",
    color: str = "#e74c3c",
    image: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Create a new token on the map."""
    if not _state.is_valid_position(x, y):
        raise ValueError(f"Position ({x}, {y}) is out of bounds")

    token_id = _state.generate_token_id()
    token = {
        "id": token_id,
        "name": name,
        "type": token_type,
        "x": x,
        "y": y,
        "hp": hp,
        "max_hp": max_hp,
        "ac": ac,
        "size": size,
        "color": color,
        "image": image,
        "conditions": [],
        "rotation": 0,
        "notes": "",
        **kwargs,
    }
    _state.tokens[token_id] = token

    if _event_bus:
        _event_bus.emit("token_spawned", {"token": token}, source="token_module")

    return token


def move_token(token_id: str, x: int, y: int) -> Dict[str, Any]:
    """Move a token to a new position."""
    token = _state.get_token(token_id)
    if not token:
        raise ValueError(f"Token not found: {token_id}")
    if not _state.is_valid_position(x, y):
        raise ValueError(f"Position ({x}, {y}) is out of bounds")

    old_x, old_y = token["x"], token["y"]
    token["x"] = x
    token["y"] = y

    if _event_bus:
        _event_bus.emit(
            "token_moved",
            {"token_id": token_id, "from": (old_x, old_y), "to": (x, y)},
            source="token_module",
        )

    return token


def remove_token(token_id: str) -> bool:
    """Remove a token from the map."""
    if token_id not in _state.tokens:
        raise ValueError(f"Token not found: {token_id}")

    token = _state.tokens.pop(token_id)

    if _event_bus:
        _event_bus.emit("token_removed", {"token": token}, source="token_module")

    return True


def update_token(token_id: str, **properties) -> Dict[str, Any]:
    """Update token properties."""
    token = _state.get_token(token_id)
    if not token:
        raise ValueError(f"Token not found: {token_id}")

    allowed = {"name", "hp", "max_hp", "ac", "size", "color", "image", "conditions", "type", "hidden", "rotation", "notes"}
    for key, value in properties.items():
        if key in allowed:
            token[key] = value

    if _event_bus:
        _event_bus.emit("token_updated", {"token": token}, source="token_module")

    return token
