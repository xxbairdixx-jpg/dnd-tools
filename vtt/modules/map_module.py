"""
Map Module

Grid management, backgrounds, fog, vision, lighting.
Emits: fog_revealed, fog_hidden, light_added, wall_added, map_background_changed
Listens to: (none)
"""

from typing import Any, Dict, List, Tuple

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
        "set_background": set_background,
        "set_map_size": set_map_size,
        "reveal_fog": reveal_fog,
        "hide_fog": hide_fog,
        "add_light": add_light,
        "remove_light": remove_light,
        "add_wall": add_wall,
        "remove_wall": remove_wall,
        "get_visible_cells": get_visible_cells,
        "measure_distance": measure_distance,
        "get_area_cells": get_area_cells,
        "set_difficult_terrain": set_difficult_terrain,
        "get_difficult_terrain": get_difficult_terrain,
    }


def set_background(url: str) -> Dict[str, Any]:
    """Set the map background image."""
    _state.map_background = url
    if _event_bus:
        _event_bus.emit("map_background_changed", {"url": url}, source="map_module")
    return {"url": url}


def set_map_size(width: int, height: int) -> Dict[str, Any]:
    """Set the map grid size."""
    _state.map_size = (width, height)
    return {"width": width, "height": height}


def reveal_fog(x: int, y: int, radius: int = 3) -> Dict[str, Any]:
    """Reveal fog in a circular area."""
    fog_entry = {"x": x, "y": y, "radius": radius, "type": "reveal"}
    _state.fog.append(fog_entry)
    if _event_bus:
        _event_bus.emit("fog_revealed", fog_entry, source="map_module")
    return fog_entry


def hide_fog(x: int, y: int, radius: int = 3) -> Dict[str, Any]:
    """Hide fog in a circular area (re-fog)."""
    fog_entry = {"x": x, "y": y, "radius": radius, "type": "hide"}
    _state.fog.append(fog_entry)
    if _event_bus:
        _event_bus.emit("fog_hidden", fog_entry, source="map_module")
    return fog_entry


def add_light(x: int, y: int, radius: int = 5, color: str = "#ffff00", bright: bool = True) -> Dict[str, Any]:
    """Add a light source to the map."""
    light = {"x": x, "y": y, "radius": radius, "color": color, "bright": bright}
    _state.lights.append(light)
    if _event_bus:
        _event_bus.emit("light_added", light, source="map_module")
    return light


def remove_light(index: int) -> bool:
    """Remove a light source by index."""
    if 0 <= index < len(_state.lights):
        _state.lights.pop(index)
        return True
    return False


def add_wall(x1: int, y1: int, x2: int, y2: int, wall_type: str = "stone") -> Dict[str, Any]:
    """Add a wall segment."""
    wall = {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "type": wall_type}
    _state.walls.append(wall)
    if _event_bus:
        _event_bus.emit("wall_added", wall, source="map_module")
    return wall


def remove_wall(index: int) -> bool:
    """Remove a wall by index."""
    if 0 <= index < len(_state.walls):
        _state.walls.pop(index)
        return True
    return False


def measure_distance(x1: int, y1: int, x2: int, y2: int) -> Dict[str, Any]:
    """Measure distance between two grid points (5ft per cell)."""
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    # D&D 5e diagonal: every other diagonal costs 10ft instead of 5ft
    diagonal = min(dx, dy)
    straight = max(dx, dy) - diagonal
    feet = (diagonal * 7.5) + (straight * 5)  # Rough 5e diagonal rule
    cells = (dx ** 2 + dy ** 2) ** 0.5
    return {
        "from": (x1, y1),
        "to": (x2, y2),
        "feet": round(feet),
        "cells": round(cells, 1),
        "dx": dx,
        "dy": dy,
    }


def get_area_cells(shape: str, origin_x: int, origin_y: int, size: int) -> List[Tuple[int, int]]:
    """Get cells affected by an area effect template."""
    cells = []
    if shape == "sphere":  # Circle (fireball, etc.)
        for dx in range(-size, size + 1):
            for dy in range(-size, size + 1):
                if (dx ** 2 + dy ** 2) ** 0.5 <= size:
                    cells.append((origin_x + dx, origin_y + dy))
    elif shape == "cube":  # Square
        for dx in range(size + 1):
            for dy in range(size + 1):
                cells.append((origin_x + dx, origin_y + dy))
    elif shape == "cone":  # 90-degree cone facing right
        for dx in range(size + 1):
            for dy in range(-dx, dx + 1):
                cells.append((origin_x + dx, origin_y + dy))
    elif shape == "line":  # Line extending right
        for dx in range(size * 2 + 1):
            cells.append((origin_x + dx, origin_y))
    return cells


def set_difficult_terrain(x: int, y: int, difficult: bool = True) -> Dict[str, Any]:
    """Mark/unmark a cell as difficult terrain."""
    if not _state.is_valid_position(x, y):
        return {"error": "Out of bounds"}
    if not hasattr(_state, 'difficult_terrain'):
        _state.difficult_terrain = set()
    if difficult:
        _state.difficult_terrain.add((x, y))
    else:
        _state.difficult_terrain.discard((x, y))
    return {"x": x, "y": y, "difficult": difficult}


def get_difficult_terrain() -> List[Tuple[int, int]]:
    """Get all difficult terrain cells."""
    if not hasattr(_state, 'difficult_terrain'):
        _state.difficult_terrain = set()
    return list(_state.difficult_terrain)


def get_visible_cells(token_id: str, sight_range: int = 60) -> List[Tuple[int, int]]:
    """
    Calculate which cells a token can see.
    Simple radius-based vision for now.
    """
    token = _state.get_token(token_id)
    if not token:
        return []

    visible = []
    tx, ty = token["x"], token["y"]
    cell_size = 5  # 5 feet per cell
    max_cells = sight_range // cell_size

    for dx in range(-max_cells, max_cells + 1):
        for dy in range(-max_cells, max_cells + 1):
            nx, ny = tx + dx, ty + dy
            if _state.is_valid_position(nx, ny):
                # Simple distance check (could add line-of-sight later)
                dist = (dx ** 2 + dy ** 2) ** 0.5
                if dist <= max_cells:
                    visible.append((nx, ny))

    return visible
