"""
Global Game State Manager

The single authoritative representation of the game world.
All state changes go through this object.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class GameState:
    """Manages the global game state."""

    def __init__(self):
        self.map_size: Tuple[int, int] = (60, 60)
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.initiative: List[str] = []
        self.turn: Optional[str] = None
        self.round: int = 0
        self.fog: List[Dict[str, Any]] = []
        self.map_background: Optional[str] = None
        self.lights: List[Dict[str, Any]] = []
        self.walls: List[Dict[str, Any]] = []
        self.combat_active: bool = False
        self.weather: str = "none"
        self.weather_intensity: int = 1
        self.pins: List[Dict[str, Any]] = []
        self.maps: Dict[str, Dict[str, Any]] = {}  # name -> { background, size, walls, lights, fog }
        self.current_map: str = "default"
        self._next_token_id: int = 1
        self._undo_stack: List[Dict[str, Any]] = []
        self._redo_stack: List[Dict[str, Any]] = []
        self._max_undo: int = 50

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            "map_size": list(self.map_size),
            "tokens": self.tokens,
            "initiative": self.initiative,
            "turn": self.turn,
            "round": self.round,
            "fog": self.fog,
            "map_background": self.map_background,
            "lights": self.lights,
            "walls": self.walls,
            "combat_active": self.combat_active,
            "weather": self.weather,
            "weather_intensity": self.weather_intensity,
            "pins": self.pins,
            "maps": self.maps,
            "current_map": self.current_map,
            "next_token_id": self._next_token_id,
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load state from dictionary."""
        self.map_size = tuple(data.get("map_size", [60, 60]))
        self.tokens = data.get("tokens", {})
        self.initiative = data.get("initiative", [])
        self.turn = data.get("turn", None)
        self.round = data.get("round", 0)
        self.fog = data.get("fog", [])
        self.map_background = data.get("map_background", None)
        self.lights = data.get("lights", [])
        self.walls = data.get("walls", [])
        self.combat_active = data.get("combat_active", False)
        self.weather = data.get("weather", "none")
        self.weather_intensity = data.get("weather_intensity", 1)
        self.pins = data.get("pins", [])
        self.maps = data.get("maps", {})
        self.current_map = data.get("current_map", "default")
        self._next_token_id = data.get("next_token_id", 1)

    def save(self, campaign_name: str) -> str:
        """Save state to a campaign file."""
        save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "campaigns")
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, f"{campaign_name}.json")
        data = self.to_dict()
        data["saved_at"] = datetime.now().isoformat()
        data["campaign_name"] = campaign_name
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return filepath

    def load(self, campaign_name: str) -> None:
        """Load state from a campaign file."""
        filepath = os.path.join(
            os.path.dirname(__file__), "..", "data", "campaigns", f"{campaign_name}.json"
        )
        with open(filepath, "r") as f:
            data = json.load(f)
        self.from_dict(data)

    def generate_token_id(self) -> str:
        """Generate a unique token ID."""
        token_id = f"token_{self._next_token_id}"
        self._next_token_id += 1
        return token_id

    def get_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Get a token by ID."""
        return self.tokens.get(token_id)

    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if a position is within map bounds."""
        return 0 <= x < self.map_size[0] and 0 <= y < self.map_size[1]

    def save_undo(self, action: str = "unknown") -> None:
        """Save current state to undo stack."""
        snapshot = {
            "action": action,
            "tokens": {k: dict(v) for k, v in self.tokens.items()},
            "walls": [dict(w) for w in self.walls],
            "fog": [dict(f) for f in self.fog],
            "lights": [dict(l) for l in self.lights],
            "pins": [dict(p) for p in self.pins],
        }
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self) -> Optional[str]:
        """Undo last action."""
        if not self._undo_stack:
            return None
        # Save current state to redo
        current = {
            "tokens": {k: dict(v) for k, v in self.tokens.items()},
            "walls": [dict(w) for w in self.walls],
            "fog": [dict(f) for f in self.fog],
            "lights": [dict(l) for l in self.lights],
            "pins": [dict(p) for p in self.pins],
        }
        self._redo_stack.append(current)
        # Restore previous state
        snapshot = self._undo_stack.pop()
        self.tokens = snapshot["tokens"]
        self.walls = snapshot["walls"]
        self.fog = snapshot["fog"]
        self.lights = snapshot["lights"]
        self.pins = snapshot["pins"]
        return snapshot.get("action", "undo")

    def redo(self) -> Optional[str]:
        """Redo last undone action."""
        if not self._redo_stack:
            return None
        # Save current state to undo
        current = {
            "tokens": {k: dict(v) for k, v in self.tokens.items()},
            "walls": [dict(w) for w in self.walls],
            "fog": [dict(f) for f in self.fog],
            "lights": [dict(l) for l in self.lights],
            "pins": [dict(p) for p in self.pins],
        }
        self._undo_stack.append(current)
        # Restore redo state
        snapshot = self._redo_stack.pop()
        self.tokens = snapshot["tokens"]
        self.walls = snapshot["walls"]
        self.fog = snapshot["fog"]
        self.lights = snapshot["lights"]
        self.pins = snapshot["pins"]
        return "redo"
