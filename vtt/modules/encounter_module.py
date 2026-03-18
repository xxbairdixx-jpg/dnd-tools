"""
Encounter Module

Encounter building, loot generation, XP calculation.
Emits: encounter_built, loot_generated
Listens to: (none)
"""

import random
from typing import Any, Dict, List

_state = None
_event_bus = None

# XP thresholds by CR
CR_XP = {
    "0": 10, "1/8": 25, "1/4": 50, "1/2": 100,
    "1": 200, "2": 450, "3": 700, "4": 1100, "5": 1800,
    "6": 2300, "7": 2900, "8": 3900, "9": 5000, "10": 5900,
    "11": 7200, "12": 8400, "13": 10000, "14": 11500, "15": 13000,
    "16": 15000, "17": 18000, "18": 20000, "19": 22000, "20": 25000,
    "21": 33000, "22": 41000, "23": 50000, "24": 62000, "25": 75000,
    "26": 90000, "27": 105000, "28": 120000, "29": 135000, "30": 155000,
}

# Loot tables by CR range
LOOT_TABLES = {
    "low": {  # CR 0-4
        "coins": [(0, 100), (0, 50), (0, 20)],  # cp, sp, gp
        "items": ["Potion of Healing", "Antitoxin", "Torch (10)", "Rations (5)", "Rope (50ft)"],
    },
    "mid": {  # CR 5-10
        "coins": [(100, 500), (50, 200), (20, 100)],
        "items": ["Potion of Greater Healing", "Potion of Invisibility", "Bag of Holding", "Cloak of Protection", "+1 Weapon"],
    },
    "high": {  # CR 11-16
        "coins": [(500, 2000), (200, 500), (100, 500)],
        "items": ["Potion of Supreme Healing", "Ring of Protection", "+2 Weapon", "Staff of Fire", "Amulet of Health"],
    },
    "epic": {  # CR 17+
        "coins": [(2000, 10000), (500, 2000), (500, 5000)],
        "items": ["Potion of Flying", "+3 Weapon", "Cloak of Invisibility", "Staff of Power", "Holy Avenger"],
    },
}


def init(state, event_bus):
    """Initialize the module."""
    global _state, _event_bus
    _state = state
    _event_bus = event_bus


def get_api() -> Dict[str, Any]:
    """Return API functions."""
    return {
        "calculate_xp": calculate_xp,
        "encounter_difficulty": encounter_difficulty,
        "generate_loot": generate_loot,
        "roll_on_table": roll_on_table,
    }


def cr_to_xp(cr: str) -> int:
    """Convert CR string to XP value."""
    return CR_XP.get(str(cr), 0)


def calculate_xp(cr_list: List[str], num_players: int = 4) -> Dict[str, Any]:
    """Calculate encounter XP with multiplier."""
    total_xp = sum(cr_to_xp(cr) for cr in cr_list)
    num_monsters = len(cr_list)

    # DMG encounter multiplier
    if num_monsters == 1:
        multiplier = 1
    elif num_monsters == 2:
        multiplier = 1.5
    elif num_monsters <= 6:
        multiplier = 2
    elif num_monsters <= 10:
        multiplier = 2.5
    elif num_monsters <= 14:
        multiplier = 3
    else:
        multiplier = 4

    adjusted_xp = int(total_xp * multiplier)
    xp_per_player = adjusted_xp // max(1, num_players)

    return {
        "base_xp": total_xp,
        "adjusted_xp": adjusted_xp,
        "xp_per_player": xp_per_player,
        "num_monsters": num_monsters,
        "multiplier": multiplier,
        "num_players": num_players,
    }


def encounter_difficulty(party_level: int, party_size: int, total_xp: int) -> str:
    """Determine encounter difficulty."""
    # XP thresholds per character level (simplified)
    thresholds = {
        1: {"easy": 25, "medium": 50, "hard": 75, "deadly": 100},
        2: {"easy": 50, "medium": 100, "hard": 150, "deadly": 200},
        3: {"easy": 75, "medium": 150, "hard": 225, "deadly": 400},
        4: {"easy": 125, "medium": 250, "hard": 375, "deadly": 500},
        5: {"easy": 250, "medium": 500, "hard": 750, "deadly": 1100},
    }
    # Default for higher levels
    for lvl in range(6, 21):
        base = thresholds[5]
        scale = 1 + (lvl - 5) * 0.3
        thresholds[lvl] = {k: int(v * scale) for k, v in base.items()}

    t = thresholds.get(party_level, thresholds[5])
    xp_per_char = total_xp // max(1, party_size)

    if xp_per_char >= t["deadly"]:
        return "💀 Deadly"
    elif xp_per_char >= t["hard"]:
        return "🔴 Hard"
    elif xp_per_char >= t["medium"]:
        return "🟡 Medium"
    elif xp_per_char >= t["easy"]:
        return "🟢 Easy"
    else:
        return "⚪ Trivial"


def generate_loot(cr: str = "1", num_items: int = None) -> Dict[str, Any]:
    """Generate random loot based on CR."""
    cr_val = _parse_cr(cr)

    if cr_val <= 4:
        table = LOOT_TABLES["low"]
    elif cr_val <= 10:
        table = LOOT_TABLES["mid"]
    elif cr_val <= 16:
        table = LOOT_TABLES["high"]
    else:
        table = LOOT_TABLES["epic"]

    # Generate coins
    cp = random.randint(*table["coins"][0]) if table["coins"][0][1] > 0 else 0
    sp = random.randint(*table["coins"][1]) if table["coins"][1][1] > 0 else 0
    gp = random.randint(*table["coins"][2]) if table["coins"][2][1] > 0 else 0

    # Generate items
    if num_items is None:
        num_items = random.randint(1, 3)
    items = random.sample(table["items"], min(num_items, len(table["items"])))

    result = {
        "coins": {"cp": cp, "sp": sp, "gp": gp},
        "items": items,
        "cr": cr,
    }

    if _event_bus:
        _event_bus.emit("loot_generated", result, source="encounter_module")

    return result


def roll_on_table(table_name: str = "loot") -> Dict[str, Any]:
    """Roll on a random table."""
    if table_name == "loot":
        return generate_loot()
    elif table_name == "wild_magic":
        effects = [
            "Roll on this table at the start of each of your turns for the next minute",
            "You cast Fireball as a 3rd-level spell centered on yourself",
            "You cast Magic Missile as a 5th-level spell",
            "You grow a long beard made of feathers",
            "You teleport 60 feet to a random unoccupied space",
            "You are frightened by the nearest creature",
            "You regain 1d10 hit points",
            "You cast Confusion centered on yourself",
        ]
        return {"effect": random.choice(effects), "roll": random.randint(1, 100)}
    return {"error": f"Unknown table: {table_name}"}


def _parse_cr(cr: str) -> float:
    """Parse CR string to float."""
    if "/" in cr:
        num, den = cr.split("/")
        return int(num) / int(den)
    try:
        return float(cr)
    except:
        return 0
