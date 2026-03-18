"""
VTT Main Entry Point

Starts the engine and web server.
"""

import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(__file__))

from engine.core import Engine
from engine.api import run_server


def main():
    engine = Engine()
    engine.start()

    # Test the engine
    print("\n🧪 Running self-test...")
    try:
        # Spawn a token
        token = engine.call_api("spawn_token", name="Test Fighter", x=5, y=5, hp=28, ac=18, color="#3498db")
        print(f"  ✅ Spawned token: {token['name']} at ({token['x']}, {token['y']})")

        # Roll dice
        roll = engine.call_api("roll_dice", expression="1d20+5")
        print(f"  ✅ Rolled {roll['expression']}: {roll['rolls']} + {roll['modifier']} = {roll['total']}")

        # Move token
        moved = engine.call_api("move_token", token_id=token["id"], x=7, y=8)
        print(f"  ✅ Moved token to ({moved['x']}, {moved['y']})")

        # Apply damage
        dmg = engine.call_api("apply_damage", token_id=token["id"], amount=10)
        print(f"  ✅ Applied {dmg['damage']} damage, HP: {dmg['hp']}/{dmg['max_hp']}")

        print("  ✅ All tests passed!\n")
    except Exception as e:
        print(f"  ❌ Test failed: {e}\n")

    # Start server
    run_server(host="0.0.0.0", port=3000, engine=engine)


if __name__ == "__main__":
    main()
