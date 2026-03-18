"""
Asset Manager

Scans asset directories and provides asset listings to the frontend.
"""

import os
import json
from typing import Any, Dict, List


class AssetManager:
    """Manages VTT assets (maps, tokens, objects)."""

    def __init__(self, assets_dir: str = None):
        if assets_dir is None:
            assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "vtt-web", "assets")
        self.assets_dir = assets_dir

    def get_maps(self) -> List[Dict[str, Any]]:
        """Get available map backgrounds."""
        maps = []
        maps_dir = os.path.join(self.assets_dir, "maps", "default")
        if os.path.exists(maps_dir):
            for f in os.listdir(maps_dir):
                if f.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    maps.append({
                        "name": f.replace('_', ' ').replace('.png', '').replace('.jpg', '').title(),
                        "file": f,
                        "url": f"/assets/maps/default/{f}",
                    })

        # Also check 2MT battle maps
        battle_dir = os.path.join(self.assets_dir, "2minutetabletop", "Battle Maps")
        if os.path.exists(battle_dir):
            for f in os.listdir(battle_dir):
                if f.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    maps.append({
                        "name": f.replace('.jpg', '').replace('.png', ''),
                        "file": f,
                        "url": f"/assets/2minutetabletop/Battle Maps/{f}",
                    })

        return maps

    def get_tokens(self) -> List[Dict[str, Any]]:
        """Get available token images."""
        tokens = []

        # Default tokens
        default_dir = os.path.join(self.assets_dir, "tokens", "default")
        if os.path.exists(default_dir):
            for f in os.listdir(default_dir):
                if f.endswith('.png'):
                    tokens.append({
                        "name": f.replace('.png', '').replace('_', ' ').title(),
                        "file": f,
                        "url": f"/assets/tokens/default/{f}",
                    })

        # 2MT tokens
        token_dir = os.path.join(self.assets_dir, "2minutetabletop", "Tokens")
        if os.path.exists(token_dir):
            for f in os.listdir(token_dir):
                if f.endswith(('.png', '.jpg', '.webp')):
                    tokens.append({
                        "name": f.replace('.png', '').replace('.jpg', '').replace('.webp', ''),
                        "file": f,
                        "url": f"/assets/2minutetabletop/Tokens/{f}",
                    })

        return tokens

    def get_objects(self) -> List[Dict[str, Any]]:
        """Get available map objects/assets."""
        objects = []
        asset_dir = os.path.join(self.assets_dir, "2minutetabletop", "Map Assets")
        if os.path.exists(asset_dir):
            for f in os.listdir(asset_dir):
                if f.endswith(('.png', '.jpg', '.webp')):
                    objects.append({
                        "name": f.replace('.png', '').replace('.jpg', '').replace('.webp', ''),
                        "file": f,
                        "url": f"/assets/2minutetabletop/Map Assets/{f}",
                    })
        return objects

    def get_all(self) -> Dict[str, List]:
        """Get all assets."""
        return {
            "maps": self.get_maps(),
            "tokens": self.get_tokens(),
            "objects": self.get_objects(),
        }
