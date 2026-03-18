"""
Dice Module

Parses dice expressions and rolls them.
Emits: dice_rolled
Listens to: (none)
"""

import random
import re
from typing import Any, Dict

_state = None
_event_bus = None


def init(state, event_bus):
    """Initialize the module with state and event bus."""
    global _state, _event_bus
    _state = state
    _event_bus = event_bus


def get_api() -> Dict[str, Any]:
    """Return API functions."""
    return {
        "roll_dice": roll_dice,
    }


def roll_dice(expression: str = "1d20") -> Dict[str, Any]:
    """
    Roll dice from an expression.

    Supported formats:
    - NdM: roll N dice with M sides (e.g., 2d6)
    - NdM+X: roll and add modifier (e.g., 1d20+5)
    - NdM-X: roll and subtract modifier
    - NdMkhN: keep highest N dice
    - NdMklN: keep lowest N dice
    """
    expression = expression.strip().lower()

    # Parse keep highest/lowest
    keep = None
    keep_type = None
    kh_match = re.search(r"(\d+)d(\d+)kh(\d+)", expression)
    kl_match = re.search(r"(\d+)d(\d+)kl(\d+)", expression)

    if kh_match:
        num, sides, keep = int(kh_match.group(1)), int(kh_match.group(2)), int(kh_match.group(3))
        keep_type = "highest"
        modifier = 0
    elif kl_match:
        num, sides, keep = int(kl_match.group(1)), int(kl_match.group(2)), int(kl_match.group(3))
        keep_type = "lowest"
        modifier = 0
    else:
        # Parse standard NdM+X or NdM-X
        match = re.match(r"^(\d+)d(\d+)([+-]\d+)?$", expression)
        if not match:
            return {"error": f"Invalid dice expression: {expression}"}
        num = int(match.group(1))
        sides = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0

    # Roll the dice
    rolls = [random.randint(1, sides) for _ in range(num)]

    # Apply keep
    if keep is not None:
        if keep_type == "highest":
            kept = sorted(rolls, reverse=True)[:keep]
        else:
            kept = sorted(rolls)[:keep]
        total = sum(kept) + modifier
    else:
        total = sum(rolls) + modifier

    result = {
        "expression": expression,
        "num": num,
        "sides": sides,
        "rolls": rolls,
        "modifier": modifier,
        "total": total,
    }

    if keep is not None:
        result["kept"] = kept
        result["keep"] = keep
        result["keep_type"] = keep_type

    # Emit event
    if _event_bus:
        _event_bus.emit("dice_rolled", result, source="dice_module")

    return result
