"""
Party Module

Party resources, calendar, time tracking.
Emits: resource_changed, calendar_advanced
Listens to: (none)
"""

from typing import Any, Dict

_state = None
_event_bus = None


def init(state, event_bus):
    """Initialize the module."""
    global _state, _event_bus
    _state = state
    _event_bus = event_bus
    if not hasattr(_state, 'party_resources'):
        _state.party_resources = {
            "gold": 0, "silver": 0, "copper": 0,
            "rations": 0, "water": 0, "torches": 0,
            "arrows": 0, "bolts": 0,
        }
    if not hasattr(_state, 'calendar'):
        _state.calendar = {
            "day": 1, "month": 1, "year": 1492,
            "hour": 8, "minute": 0,
            "season": "spring",
            "weather": "clear",
        }


def get_api() -> Dict[str, Any]:
    """Return API functions."""
    return {
        "get_resources": get_resources,
        "set_resource": set_resource,
        "get_calendar": get_calendar,
        "advance_time": advance_time,
        "set_date": set_date,
    }


def get_resources() -> Dict[str, Any]:
    """Get party resources."""
    return _state.party_resources


def set_resource(resource: str, amount: int) -> Dict[str, Any]:
    """Set a party resource value."""
    if resource in _state.party_resources:
        _state.party_resources[resource] = amount
        if _event_bus:
            _event_bus.emit("resource_changed", {"resource": resource, "amount": amount}, source="party_module")
    return _state.party_resources


def get_calendar() -> Dict[str, Any]:
    """Get current calendar date/time."""
    return _state.calendar


def advance_time(hours: int = 1, minutes: int = 0) -> Dict[str, Any]:
    """Advance the in-game calendar."""
    cal = _state.calendar
    cal["minute"] += minutes
    cal["hour"] += hours + cal["minute"] // 60
    cal["minute"] = cal["minute"] % 60

    while cal["hour"] >= 24:
        cal["hour"] -= 24
        cal["day"] += 1

    # Month lengths ( Forgotten Realms calendar)
    month_days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_names = ["Hammer", "Alturiak", "Ches", "Tarsakh", "Mirtul", "Kythorn",
                   "Eleasis", "Eleint", "Marpenoth", "Uktar", "Nightal"]

    while cal["month"] <= 12 and cal["day"] > month_days[cal["month"] - 1]:
        cal["day"] -= month_days[cal["month"] - 1]
        cal["month"] += 1
        if cal["month"] > 12:
            cal["month"] = 1
            cal["year"] += 1

    # Season
    if cal["month"] in [12, 1, 2]:
        cal["season"] = "winter"
    elif cal["month"] in [3, 4, 5]:
        cal["season"] = "spring"
    elif cal["month"] in [6, 7, 8]:
        cal["season"] = "summer"
    else:
        cal["season"] = "autumn"

    if _event_bus:
        _event_bus.emit("calendar_advanced", cal.copy(), source="party_module")

    return cal


def set_date(day: int = 1, month: int = 1, year: int = 1492, hour: int = 8) -> Dict[str, Any]:
    """Set the calendar date."""
    _state.calendar["day"] = day
    _state.calendar["month"] = month
    _state.calendar["year"] = year
    _state.calendar["hour"] = hour
    return _state.calendar
