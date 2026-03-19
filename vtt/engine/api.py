"""
API Layer — REST + WebSocket

Exposes module API functions as HTTP endpoints.
Serves static web files.
"""

import json
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_sock import Sock

from .core import Engine
from .asset_manager import AssetManager


def create_app(engine: Engine = None) -> Flask:
    """Create the Flask app with all routes."""
    if engine is None:
        engine = Engine()
        engine.start()

    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "..", "web"))
    sock = Sock(app)
    ws_clients = []
    assets = AssetManager()

    # Serve assets from vtt-web/assets/
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "vtt-web", "assets")

    def broadcast(data: dict):
        """Send data to all WebSocket clients."""
        msg = json.dumps(data)
        dead = []
        for ws in ws_clients:
            try:
                ws.send(msg)
            except:
                dead.append(ws)
        for ws in dead:
            ws_clients.remove(ws)

    # Subscribe to all events and broadcast
    def on_any_event(event):
        broadcast({"type": "event", "event": event})

    engine.event_bus.subscribe("*", on_any_event)

    # --- REST Endpoints ---

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.route("/<path:path>")
    def static_files(path):
        return send_from_directory(app.static_folder, path)

    @app.route("/api/state", methods=["GET"])
    def get_state():
        return jsonify(engine.get_state())

    @app.route("/api/token/add", methods=["POST"])
    def add_token():
        data = request.json
        engine.state.save_undo("add_token")
        result = engine.call_api("spawn_token", **data)
        broadcast({"type": "token_added", "token": result})
        return jsonify({"success": True, "token": result})

    @app.route("/api/token/move", methods=["POST"])
    def move_token():
        data = request.json
        engine.state.save_undo("move_token")
        result = engine.call_api("move_token", **data)
        broadcast({"type": "token_moved", **data})
        return jsonify({"success": True})

    @app.route("/api/token/remove", methods=["POST"])
    def remove_token():
        data = request.json
        engine.state.save_undo("remove_token")
        engine.call_api("remove_token", token_id=data["id"])
        broadcast({"type": "token_removed", "id": data["id"]})
        return jsonify({"success": True})

    @app.route("/api/token/update", methods=["POST"])
    def update_token():
        data = request.json
        result = engine.call_api("update_token", **data)
        broadcast({"type": "token_updated", "token": result})
        return jsonify({"success": True, "token": result})

    @app.route("/api/roll", methods=["POST"])
    def roll_dice():
        data = request.json
        result = engine.call_api("roll_dice", expression=data.get("notation", "1d20"))
        chat_msg = {
            "sender": data.get("roller", "GM"),
            "text": f"🎲 {result['expression']}: [{', '.join(map(str, result['rolls']))}] = **{result['total']}**",
            "isRoll": True,
        }
        broadcast({"type": "chat", "message": chat_msg})
        return jsonify(result)

    @app.route("/api/chat", methods=["POST"])
    def send_chat():
        data = request.json
        chat_msg = {"sender": data.get("sender", "GM"), "text": data["text"]}
        broadcast({"type": "chat", "message": chat_msg})
        return jsonify({"success": True})

    @app.route("/api/combat/start", methods=["POST"])
    def start_combat():
        result = engine.call_api("start_combat")
        broadcast({"type": "combat_started", **result})
        return jsonify(result)

    @app.route("/api/combat/end-turn", methods=["POST"])
    def end_turn():
        result = engine.call_api("end_turn")
        broadcast({"type": "turn_ended", **result})
        return jsonify(result)

    @app.route("/api/combat/damage", methods=["POST"])
    def apply_damage():
        data = request.json
        result = engine.call_api("apply_damage", **data)
        broadcast({"type": "damage_applied", **result})
        return jsonify(result)

    @app.route("/api/combat/heal", methods=["POST"])
    def apply_heal():
        data = request.json
        result = engine.call_api("apply_heal", **data)
        broadcast({"type": "heal_applied", **result})
        return jsonify(result)

    @app.route("/api/combat/condition/add", methods=["POST"])
    def add_condition():
        data = request.json
        result = engine.call_api("add_condition", token_id=data["token_id"], condition=data["condition"])
        broadcast({"type": "condition_added", **result})
        return jsonify(result)

    @app.route("/api/combat/condition/remove", methods=["POST"])
    def remove_condition():
        data = request.json
        result = engine.call_api("remove_condition", token_id=data["token_id"], condition=data["condition"])
        broadcast({"type": "condition_removed", **result})
        return jsonify(result)

    @app.route("/api/combat/concentration", methods=["POST"])
    def set_concentration():
        data = request.json
        result = engine.call_api("set_concentration", token_id=data["token_id"], spell=data.get("spell", ""), dc=data.get("dc", 10))
        broadcast({"type": "concentration_set", **result})
        return jsonify(result)

    @app.route("/api/combat/concentration/break", methods=["POST"])
    def break_concentration():
        data = request.json
        result = engine.call_api("break_concentration", token_id=data["token_id"])
        broadcast({"type": "concentration_broken", **result})
        return jsonify(result)

    @app.route("/api/combat/death-save", methods=["POST"])
    def death_save():
        data = request.json
        result = engine.call_api("death_save", token_id=data["token_id"], success=data.get("success", True))
        broadcast({"type": "death_save", **result})
        return jsonify(result)

    @app.route("/api/combat/death-saves/reset", methods=["POST"])
    def reset_death_saves():
        data = request.json
        result = engine.call_api("reset_death_saves", token_id=data["token_id"])
        return jsonify(result)

    @app.route("/api/combat/short-rest", methods=["POST"])
    def short_rest():
        data = request.json or {}
        result = engine.call_api("short_rest", token_ids=data.get("token_ids"))
        broadcast({"type": "short_rest", **result})
        return jsonify(result)

    @app.route("/api/combat/long-rest", methods=["POST"])
    def long_rest():
        data = request.json or {}
        result = engine.call_api("long_rest", token_ids=data.get("token_ids"))
        broadcast({"type": "long_rest", **result})
        return jsonify(result)

    @app.route("/api/combat/roll-initiative", methods=["POST"])
    def roll_initiative():
        data = request.json or {}
        result = engine.call_api("roll_initiative", token_ids=data.get("token_ids"))
        return jsonify(result)

    @app.route("/api/pathfind", methods=["POST"])
    def pathfind():
        """Find path from token to target, avoiding walls."""
        data = request.json
        x1, y1 = data["x1"], data["y1"]
        x2, y2 = data["x2"], data["y2"]
        # Simple A* pathfinding
        import heapq
        walls = set()
        for w in engine.state.walls:
            # Mark wall cells (simplified)
            if w["x1"] == w["x2"]:  # Vertical wall
                for y in range(min(w["y1"], w["y2"]), max(w["y1"], w["y2"]) + 1):
                    walls.add((w["x1"], y))
            else:  # Horizontal wall
                for x in range(min(w["x1"], w["x2"]), max(w["x1"], w["x2"]) + 1):
                    walls.add((x, w["y1"]))

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        start = (x1, y1)
        goal = (x2, y2)
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return jsonify({"path": path, "length": len(path) - 1})

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if (0 <= neighbor[0] < engine.state.map_size[0] and
                    0 <= neighbor[1] < engine.state.map_size[1] and
                    neighbor not in walls):
                    tentative = g_score[current] + 1
                    if tentative < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative
                        heapq.heappush(open_set, (tentative + heuristic(neighbor, goal), neighbor))

        return jsonify({"path": [], "length": -1, "error": "No path found"})

    @app.route("/api/map/background", methods=["POST"])
    def set_background():
        data = request.json
        engine.state.map_background = data["url"]
        broadcast({"type": "map_background", "url": data["url"]})
        return jsonify({"success": True})

    @app.route("/api/map/save", methods=["POST"])
    def save_current_map():
        """Save current map state to named map."""
        data = request.json
        name = data.get("name", engine.state.current_map)
        engine.state.maps[name] = {
            "background": engine.state.map_background,
            "map_size": list(engine.state.map_size),
            "walls": [dict(w) for w in engine.state.walls],
            "lights": [dict(l) for l in engine.state.lights],
            "fog": [dict(f) for f in engine.state.fog],
            "pins": [dict(p) for p in engine.state.pins],
        }
        engine.state.current_map = name
        return jsonify({"success": True, "name": name})

    @app.route("/api/map/switch", methods=["POST"])
    def switch_map():
        """Switch to a saved map."""
        data = request.json
        name = data.get("name", "default")
        # Save current map first
        engine.state.maps[engine.state.current_map] = {
            "background": engine.state.map_background,
            "map_size": list(engine.state.map_size),
            "walls": [dict(w) for w in engine.state.walls],
            "lights": [dict(l) for l in engine.state.lights],
            "fog": [dict(f) for f in engine.state.fog],
            "pins": [dict(p) for p in engine.state.pins],
        }
        # Load target map
        if name in engine.state.maps:
            m = engine.state.maps[name]
            engine.state.map_background = m.get("background")
            engine.state.map_size = tuple(m.get("map_size", [60, 60]))
            engine.state.walls = m.get("walls", [])
            engine.state.lights = m.get("lights", [])
            engine.state.fog = m.get("fog", [])
            engine.state.pins = m.get("pins", [])
            engine.state.current_map = name
            broadcast({"type": "state", "data": engine.get_state()})
            return jsonify({"success": True, "name": name})
        return jsonify({"error": f"Map '{name}' not found"}), 404

    @app.route("/api/map/list", methods=["GET"])
    def list_maps():
        """List all saved maps."""
        maps = [{"name": k, "background": v.get("background", "")} for k, v in engine.state.maps.items()]
        return jsonify({"maps": maps, "current": engine.state.current_map})

    @app.route("/api/terrain/set", methods=["POST"])
    def set_terrain():
        data = request.json
        result = engine.call_api("set_difficult_terrain", x=data["x"], y=data["y"], difficult=data.get("difficult", True))
        broadcast({"type": "terrain_changed", **result})
        return jsonify(result)

    @app.route("/api/terrain/get", methods=["GET"])
    def get_terrain():
        result = engine.call_api("get_difficult_terrain")
        return jsonify({"cells": [list(c) for c in result]})

    @app.route("/api/token/rotate", methods=["POST"])
    def rotate_token():
        data = request.json
        token = engine.state.get_token(data["token_id"])
        if not token:
            return jsonify({"error": "Token not found"}), 404
        token["rotation"] = (token.get("rotation", 0) + data.get("degrees", 90)) % 360
        broadcast({"type": "token_updated", "token": token})
        return jsonify({"success": True, "rotation": token["rotation"]})

    @app.route("/api/grid/size", methods=["POST"])
    def set_grid_size():
        data = request.json
        engine.state.map_size = (data.get("width", 60), data.get("height", 40))
        broadcast({"type": "state", "data": engine.get_state()})
        return jsonify({"width": engine.state.map_size[0], "height": engine.state.map_size[1]})

    @app.route("/api/export", methods=["GET"])
    def export_state():
        """Export full game state as JSON."""
        return jsonify(engine.get_state())

    @app.route("/api/import", methods=["POST"])
    def import_state():
        """Import game state from JSON."""
        data = request.json
        engine.state.from_dict(data)
        broadcast({"type": "state", "data": engine.get_state()})
        return jsonify({"success": True})

    @app.route("/api/sound/zone", methods=["POST"])
    def add_sound_zone():
        data = request.json
        zone = {"x": data["x"], "y": data["y"], "radius": data.get("radius", 5), "sound": data.get("sound", ""), "loop": data.get("loop", True)}
        if not hasattr(engine.state, 'sound_zones'):
            engine.state.sound_zones = []
        engine.state.sound_zones.append(zone)
        broadcast({"type": "sound_zone_added", "zone": zone})
        return jsonify(zone)

    @app.route("/api/sound/zones", methods=["GET"])
    def get_sound_zones():
        return jsonify(getattr(engine.state, 'sound_zones', []))

    @app.route("/api/sound/zone/remove", methods=["POST"])
    def remove_sound_zone():
        data = request.json
        if hasattr(engine.state, 'sound_zones'):
            engine.state.sound_zones = [z for z in engine.state.sound_zones if not (z["x"] == data["x"] and z["y"] == data["y"])]
        return jsonify({"success": True})

    @app.route("/api/fog/reveal", methods=["POST"])
    def reveal_fog():
        data = request.json
        result = engine.call_api("reveal_fog", **data)
        broadcast({"type": "fog_revealed", **result})
        return jsonify(result)

    @app.route("/api/measure", methods=["POST"])
    def measure():
        data = request.json
        result = engine.call_api("measure_distance", x1=data["x1"], y1=data["y1"], x2=data["x2"], y2=data["y2"])
        return jsonify(result)

    @app.route("/api/area", methods=["POST"])
    def area_template():
        data = request.json
        result = engine.call_api("get_area_cells", shape=data["shape"], origin_x=data["x"], origin_y=data["y"], size=data["size"])
        return jsonify({"cells": result})

    @app.route("/api/wall/add", methods=["POST"])
    def add_wall():
        data = request.json
        result = engine.call_api("add_wall", x1=data["x1"], y1=data["y1"], x2=data["x2"], y2=data["y2"], wall_type=data.get("wall_type", "stone"))
        broadcast({"type": "wall_added", "wall": result})
        return jsonify(result)

    @app.route("/api/campaign/save", methods=["POST"])
    def save_campaign():
        data = request.json
        name = data.get("name", "default")
        filepath = engine.state.save(name)
        return jsonify({"success": True, "file": filepath, "name": name})

    @app.route("/api/campaign/load", methods=["POST"])
    def load_campaign():
        data = request.json
        name = data.get("name", "default")
        try:
            engine.state.load(name)
            broadcast({"type": "state", "data": engine.get_state()})
            return jsonify({"success": True, "name": name})
        except FileNotFoundError:
            return jsonify({"error": f"Campaign '{name}' not found"}), 404

    @app.route("/api/campaign/list", methods=["GET"])
    def list_campaigns():
        import glob
        save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "campaigns")
        files = glob.glob(os.path.join(save_dir, "*.json"))
        campaigns = [{"name": os.path.basename(f).replace(".json", ""), "modified": os.path.getmtime(f)} for f in files]
        return jsonify(campaigns)

    @app.route("/api/weather/set", methods=["POST"])
    def set_weather():
        data = request.json
        engine.state.weather = data.get("type", "none")
        engine.state.weather_intensity = data.get("intensity", 1)
        broadcast({"type": "weather_changed", "weather": engine.state.weather, "intensity": engine.state.weather_intensity})
        return jsonify({"weather": engine.state.weather, "intensity": engine.state.weather_intensity})

    @app.route("/api/pin/add", methods=["POST"])
    def add_pin():
        data = request.json
        pin = {"x": data["x"], "y": data["y"], "label": data.get("label", ""), "color": data.get("color", "#f1c40f")}
        if not hasattr(engine.state, 'pins'):
            engine.state.pins = []
        engine.state.pins.append(pin)
        broadcast({"type": "pin_added", "pin": pin})
        return jsonify(pin)

    @app.route("/api/pin/remove", methods=["POST"])
    def remove_pin():
        data = request.json
        if hasattr(engine.state, 'pins'):
            engine.state.pins = [p for p in engine.state.pins if not (p["x"] == data["x"] and p["y"] == data["y"])]
        return jsonify({"success": True})

    @app.route("/api/encounter/xp", methods=["POST"])
    def calc_xp():
        data = request.json
        result = engine.call_api("calculate_xp", cr_list=data["cr_list"], num_players=data.get("num_players", 4))
        return jsonify(result)

    @app.route("/api/encounter/difficulty", methods=["POST"])
    def encounter_diff():
        data = request.json
        result = engine.call_api("encounter_difficulty", party_level=data["party_level"], party_size=data["party_size"], total_xp=data["total_xp"])
        return jsonify({"difficulty": result})

    @app.route("/api/loot/generate", methods=["POST"])
    def gen_loot():
        data = request.json
        result = engine.call_api("generate_loot", cr=data.get("cr", "1"), num_items=data.get("num_items"))
        return jsonify(result)

    @app.route("/api/party/resources", methods=["GET"])
    def get_resources():
        return jsonify(engine.call_api("get_resources"))

    @app.route("/api/party/resource", methods=["POST"])
    def set_resource():
        data = request.json
        result = engine.call_api("set_resource", resource=data["resource"], amount=data["amount"])
        return jsonify(result)

    @app.route("/api/calendar", methods=["GET"])
    def get_calendar():
        return jsonify(engine.call_api("get_calendar"))

    @app.route("/api/calendar/advance", methods=["POST"])
    def advance_time():
        data = request.json
        result = engine.call_api("advance_time", hours=data.get("hours", 1), minutes=data.get("minutes", 0))
        broadcast({"type": "calendar_changed", "calendar": result})
        return jsonify(result)

    @app.route("/api/rules/search", methods=["POST"])
    def search_rules():
        data = request.json
        query = data.get("query", "").lower()
        refs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "references")
        results = []
        for fname in os.listdir(refs_dir):
            if fname.endswith('.md'):
                filepath = os.path.join(refs_dir, fname)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    if query in content.lower():
                        # Find matching lines
                        lines = content.split('\n')
                        matches = []
                        for i, line in enumerate(lines):
                            if query in line.lower():
                                start = max(0, i - 1)
                                end = min(len(lines), i + 3)
                                matches.append('\n'.join(lines[start:end]))
                        if matches:
                            results.append({"file": fname, "matches": matches[:3]})
                except:
                    pass
        return jsonify(results)

    @app.route("/api/rules/list", methods=["GET"])
    def list_rules():
        refs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "references")
        files = []
        for fname in sorted(os.listdir(refs_dir)):
            if fname.endswith('.md'):
                filepath = os.path.join(refs_dir, fname)
                size = os.path.getsize(filepath)
                files.append({"name": fname, "size": size})
        return jsonify(files)

    @app.route("/api/rules/get/<filename>", methods=["GET"])
    def get_rules_file(filename):
        refs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "references")
        filepath = os.path.join(refs_dir, filename)
        if not os.path.exists(filepath):
            return jsonify({"error": "File not found"}), 404
        with open(filepath, 'r') as f:
            content = f.read()
        return jsonify({"filename": filename, "content": content[:50000]})

    @app.route("/api/undo", methods=["POST"])
    def undo_action():
        action = engine.state.undo()
        if action:
            broadcast({"type": "state", "data": engine.get_state()})
            return jsonify({"success": True, "action": action})
        return jsonify({"success": False, "error": "Nothing to undo"})

    @app.route("/api/redo", methods=["POST"])
    def redo_action():
        action = engine.state.redo()
        if action:
            broadcast({"type": "state", "data": engine.get_state()})
            return jsonify({"success": True, "action": action})
        return jsonify({"success": False, "error": "Nothing to redo"})

    @app.route("/api/effect", methods=["POST"])
    def add_effect():
        data = request.json
        broadcast({"type": "effect", "effect": data})
        return jsonify({"success": True})

    @app.route("/api/tokens", methods=["GET"])
    def list_tokens():
        return jsonify(engine.state.tokens)

    # --- Asset Endpoints ---

    @app.route("/api/assets", methods=["GET"])
    def get_all_assets():
        return jsonify(assets.get_all())

    @app.route("/api/assets/maps", methods=["GET"])
    def get_map_assets():
        return jsonify(assets.get_maps())

    @app.route("/api/assets/tokens", methods=["GET"])
    def get_token_assets():
        return jsonify(assets.get_tokens())

    @app.route("/api/assets/objects", methods=["GET"])
    def get_object_assets():
        return jsonify(assets.get_objects())

    @app.route("/assets/<path:filename>")
    def serve_asset(filename):
        """Serve asset files from vtt-web/assets/"""
        return send_from_directory(assets_dir, filename)

    # --- WebSocket ---

    @sock.route("/ws")
    def websocket(ws):
        ws_clients.append(ws)
        ws.send(json.dumps({"type": "state", "data": engine.get_state()}))
        try:
            while True:
                msg = ws.receive()
                if msg:
                    data = json.loads(msg)
                    handle_ws_message(data, ws)
        except:
            pass
        finally:
            if ws in ws_clients:
                ws_clients.remove(ws)

    def handle_ws_message(data: dict, ws):
        """Handle incoming WebSocket messages."""
        msg_type = data.get("type")
        if msg_type == "move":
            engine.call_api("move_token", token_id=data["id"], x=data["x"], y=data["y"])
            broadcast({"type": "token_moved", "id": data["id"], "x": data["x"], "y": data["y"]})
        elif msg_type == "chat":
            chat_msg = {"sender": data.get("sender", "Player"), "text": data["text"]}
            broadcast({"type": "chat", "message": chat_msg})

    return app


def run_server(host: str = "0.0.0.0", port: int = 3000, engine: Engine = None):
    """Run the VTT server."""
    app = create_app(engine)
    print(f"🌐 VTT Server running on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
