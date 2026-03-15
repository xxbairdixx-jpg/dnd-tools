#!/usr/bin/env python3
"""
Battlemap Generator - Creates basic grid maps
Tries Pollinations.ai first, falls back to local placeholder
"""

import sys, os, urllib.request, urllib.parse, random
from PIL import Image, ImageDraw, ImageFont

OUTDIR = os.path.expanduser("~/voice-profiles/maps")
os.makedirs(OUTDIR, exist_ok=True)

def try_pollinations(prompt, filename):
    """Try to generate via Pollinations.ai"""
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={random.randint(1,999999)}"
    outfile = os.path.join(OUTDIR, f"{filename}.jpg")
    try:
        print(f"🌐 Trying Pollinations.ai...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(outfile, 'wb') as f:
                f.write(resp.read())
        # Check if it's actually an image
        with Image.open(outfile) as img:
            img.verify()
        print(f"✅ Generated via Pollinations: {outfile}")
        return True
    except Exception as e:
        print(f"⚠️  Pollinations failed: {e}")
        return False

def generate_placeholder(filename, map_type="dungeon", grid_w=30, grid_h=20):
    """Generate a basic placeholder battlemap"""
    cell_size = 40
    img_w = grid_w * cell_size
    img_h = grid_h * cell_size
    
    # Colors by map type
    themes = {
        "dungeon": {"floor": "#4a4a4a", "wall": "#2a2a2a", "accent": "#3a3a3a"},
        "forest": {"floor": "#2d4a2d", "wall": "#1a3a1a", "accent": "#3d5a3d"},
        "tavern": {"floor": "#6a5a3a", "wall": "#4a3a2a", "accent": "#7a6a4a"},
        "cave": {"floor": "#3a3a3a", "wall": "#1a1a1a", "accent": "#4a4a4a"},
        "village": {"floor": "#5a6a4a", "wall": "#7a6a4a", "accent": "#4a5a3a"},
        "castle": {"floor": "#5a5a6a", "wall": "#3a3a4a", "accent": "#6a6a7a"},
    }
    theme = themes.get(map_type, themes["dungeon"])
    
    img = Image.new('RGB', (img_w, img_h), theme["floor"])
    draw = ImageDraw.Draw(img)
    
    # Draw grid
    for x in range(0, img_w, cell_size):
        draw.line([(x, 0), (x, img_h)], fill="#333333", width=1)
    for y in range(0, img_h, cell_size):
        draw.line([(0, y), (img_w, y)], fill="#333333", width=1)
    
    # Add some random walls/features
    for _ in range(grid_w * grid_h // 8):
        rx = random.randint(0, grid_w - 1) * cell_size
        ry = random.randint(0, grid_h - 1) * cell_size
        if random.random() > 0.5:
            draw.rectangle([rx+2, ry+2, rx+cell_size-2, ry+cell_size-2], fill=theme["wall"])
        else:
            draw.rectangle([rx+4, ry+4, rx+cell_size-4, ry+cell_size-4], fill=theme["accent"])
    
    # Add border walls
    for x in range(0, img_w, cell_size):
        draw.rectangle([x, 0, x+cell_size-1, cell_size-1], fill=theme["wall"])
        draw.rectangle([x, img_h-cell_size, x+cell_size-1, img_h-1], fill=theme["wall"])
    for y in range(0, img_h, cell_size):
        draw.rectangle([0, y, cell_size-1, y+cell_size-1], fill=theme["wall"])
        draw.rectangle([img_w-cell_size, y, img_w-1, y+cell_size-1], fill=theme["wall"])
    
    # Label
    try:
        font = ImageFont.truetype("/system/fonts/DroidSans.ttf", 24)
    except:
        font = ImageFont.load_default()
    draw.text((img_w//2 - 80, img_h//2 - 12), f"{map_type.upper()} BATTLEMAP", fill="#888888", font=font)
    
    outfile = os.path.join(OUTDIR, f"{filename}.jpg")
    img.save(outfile, "JPEG", quality=85)
    print(f"✅ Placeholder saved: {outfile}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 generate-map.py <prompt> [filename] [map_type]")
        print("Map types: dungeon, forest, tavern, cave, village, castle")
        sys.exit(1)
    
    prompt = sys.argv[1]
    filename = sys.argv[2] if len(sys.argv) > 2 else "battlemap"
    map_type = sys.argv[3] if len(sys.argv) > 3 else "dungeon"
    
    # Try Pollinations first, fall back to placeholder
    if not try_pollinations(prompt, filename):
        print(f"🎨 Generating local placeholder ({map_type})...")
        generate_placeholder(filename, map_type)
