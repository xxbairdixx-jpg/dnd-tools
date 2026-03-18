"""
Event System

Modules communicate through events (pub/sub pattern).
No direct dependencies between modules.
"""

from datetime import datetime
from typing import Any, Callable, Dict, List


class EventBus:
    """Publish/subscribe event system for module communication."""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._event_log: List[Dict[str, Any]] = []

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Register a listener for an event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Remove a listener for an event type."""
        if event_type in self._listeners:
            self._listeners[event_type] = [
                cb for cb in self._listeners[event_type] if cb != callback
            ]

    def emit(self, event_type: str, data: Dict[str, Any] = None, source: str = "unknown") -> None:
        """Dispatch an event to all registered listeners."""
        event = {
            "type": event_type,
            "data": data or {},
            "source": source,
            "timestamp": datetime.now().isoformat(),
        }
        self._event_log.append(event)

        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event listener for {event_type}: {e}")

    def get_log(self, event_type: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events from the log."""
        if event_type:
            filtered = [e for e in self._event_log if e["type"] == event_type]
            return filtered[-limit:]
        return self._event_log[-limit:]

    def clear_log(self) -> None:
        """Clear the event log."""
        self._event_log.clear()


# Standard event types
class Events:
    # Token events
    TOKEN_SPAWNED = "token_spawned"
    TOKEN_MOVED = "token_moved"
    TOKEN_REMOVED = "token_removed"
    TOKEN_UPDATED = "token_updated"

    # Combat events
    COMBAT_STARTED = "combat_started"
    COMBAT_ENDED = "combat_ended"
    TURN_STARTED = "turn_started"
    TURN_ENDED = "turn_ended"
    ROUND_STARTED = "round_started"

    # Damage/healing events
    DAMAGE_APPLIED = "damage_applied"
    HEAL_APPLIED = "heal_applied"

    # Condition events
    CONDITION_ADDED = "condition_added"
    CONDITION_REMOVED = "condition_removed"

    # Dice events
    DICE_ROLLED = "dice_rolled"

    # Map events
    FOG_REVEALED = "fog_revealed"
    FOG_HIDDEN = "fog_hidden"
    LIGHT_ADDED = "light_added"
    WALL_ADDED = "wall_added"
    MAP_BACKGROUND_CHANGED = "map_background_changed"
