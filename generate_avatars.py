"""
Generate SVG character avatar images for all 72 characters in the Keroro Archive.
Reads characters.json, generates SVG avatars, updates characters.json and keroro.db.
"""

import json
import os
import sqlite3
import math
import re

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARACTERS_JSON = os.path.join(BASE_DIR, "data", "characters.json")
DB_PATH = os.path.join(BASE_DIR, "data", "keroro.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "web", "images", "characters")

# Color mapping from color names to hex
COLOR_MAP = {
    "green": "#4CAF50",
    "red": "#F44336",
    "dark blue": "#1565C0",
    "yellow": "#FFC107",
    "blue": "#2196F3",
    "purple": "#9C27B0",
    "light blue": "#03A9F4",
    "orange": "#FF9800",
    "gray": "#9E9E9E",
    "pink": "#E91E63",
    "dark green": "#2E7D32",
    "light green": "#81C784",
    "crimson": "#DC143C",
    "brown": "#795548",
    "gold-brown": "#B8860B",
    "silver": "#C0C0C0",
    "white": "#F5F5F5",
    "dark purple": "#4A148C",
    "dark gray": "#616161",
    "aqua": "#00BCD4",
    "peach": "#FFAB91",
    "black": "#212121",
    "olive green": "#827717",
    "dark red": "#B71C1C",
    "tan": "#D2B48C",
    "light purple": "#CE93D8",
    "light pink": "#F8BBD0",
    "light brown": "#A1887F",
    "pale blue": "#B3E5FC",
    "bright green": "#69F0AE",
    "calico": "#F4A460",
    "dark metallic": "#37474F",
    "translucent blue": "#80DEEA",
    # Compound colors - use first color
    "green-black": "#4CAF50",
    "red-black": "#F44336",
    "dark green-black": "#2E7D32",
    "orange-brown": "#FF9800",
    "white-blue": "#E3F2FD",
    "blue-white": "#BBDEFB",
    "purple-black": "#6A1B9A",
    "dark blue-black": "#0D47A1",
    "dark red-purple": "#880E4F",
    "silver-mechanical": "#B0BEC5",
    "gold-white": "#FFD54F",
    "green-metallic": "#66BB6A",
    "pink-orange": "#FF8A80",
}

DEFAULT_COLOR = "#78909C"  # blue-gray for null/unknown


def get_hex_color(color_name):
    """Get hex color from color name, handling None and unknown values."""
    if color_name is None:
        return DEFAULT_COLOR
    color_lower = color_name.lower().strip()
    if color_lower in COLOR_MAP:
        return COLOR_MAP[color_lower]
    # Try first part of compound color
    first = color_lower.split("-")[0].split("/")[0].strip()
    if first in COLOR_MAP:
        return COLOR_MAP[first]
    return DEFAULT_COLOR


def darken_color(hex_color, factor=0.7):
    """Darken a hex color by a factor."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return f"#{r:02X}{g:02X}{b:02X}"


def lighten_color(hex_color, factor=0.3):
    """Lighten a hex color by mixing with white."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02X}{g:02X}{b:02X}"


def star_points(cx, cy, outer_r, inner_r, n=5):
    """Generate points for an n-pointed star."""
    points = []
    for i in range(n * 2):
        angle = math.pi / 2 + i * math.pi / n
        r = outer_r if i % 2 == 0 else inner_r
        x = cx + r * math.cos(angle)
        y = cy - r * math.sin(angle)
        points.append(f"{x:.1f},{y:.1f}")
    return " ".join(points)


def generate_keronian_svg(color_hex, char_id):
    """Generate SVG for a Keronian (frog-like alien) character."""
    body_color = color_hex
    dark_color = darken_color(color_hex, 0.65)
    light_color = lighten_color(color_hex, 0.3)
    star_color = darken_color(color_hex, 0.5)

    # Keron star points
    keron_star = star_points(60, 82, 12, 5, 5)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <defs>
    <radialGradient id="bg{char_id}" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="{light_color}"/>
      <stop offset="100%" stop-color="{body_color}"/>
    </radialGradient>
  </defs>
  <!-- Background circle -->
  <circle cx="60" cy="60" r="58" fill="#F5F5F5" stroke="#E0E0E0" stroke-width="2"/>
  <!-- Body/head -->
  <ellipse cx="60" cy="62" rx="38" ry="36" fill="url(#bg{char_id})" stroke="{dark_color}" stroke-width="1.5"/>
  <!-- Head top bump (Keronian hat shape) -->
  <ellipse cx="60" cy="32" rx="22" ry="14" fill="{body_color}" stroke="{dark_color}" stroke-width="1.5"/>
  <!-- Left eye white -->
  <ellipse cx="42" cy="48" rx="14" ry="16" fill="white" stroke="{dark_color}" stroke-width="1"/>
  <!-- Right eye white -->
  <ellipse cx="78" cy="48" rx="14" ry="16" fill="white" stroke="{dark_color}" stroke-width="1"/>
  <!-- Left pupil -->
  <ellipse cx="44" cy="50" rx="6" ry="8" fill="#212121"/>
  <ellipse cx="46" cy="47" rx="2.5" ry="3" fill="white"/>
  <!-- Right pupil -->
  <ellipse cx="76" cy="50" rx="6" ry="8" fill="#212121"/>
  <ellipse cx="78" cy="47" rx="2.5" ry="3" fill="white"/>
  <!-- Mouth (smile) -->
  <path d="M 48 68 Q 60 78 72 68" fill="none" stroke="{dark_color}" stroke-width="2" stroke-linecap="round"/>
  <!-- Keron Star on belly -->
  <polygon points="{keron_star}" fill="{star_color}" stroke="{darken_color(star_color, 0.7)}" stroke-width="1"/>
</svg>'''
    return svg


def generate_human_svg(char_id, name):
    """Generate SVG for a Human character."""
    # Assign different hair and skin tones based on character id for variety
    skin_tones = ["#FFDBB4", "#F5CBA7", "#EDBB99", "#D5B895", "#F0D5B8"]
    hair_colors = ["#3E2723", "#212121", "#4E342E", "#5D4037", "#795548",
                   "#FF8A65", "#D84315", "#1B5E20", "#BF360C", "#263238"]
    hair_styles = ["short", "long", "spiky", "bob", "ponytail"]

    skin = skin_tones[char_id % len(skin_tones)]
    hair = hair_colors[char_id % len(hair_colors)]
    style = hair_styles[char_id % len(hair_styles)]
    dark_skin = darken_color(skin, 0.85)

    # Hair path based on style
    if style == "short":
        hair_path = f'<path d="M 30 52 Q 30 22 60 18 Q 90 22 90 52 L 85 45 Q 82 25 60 22 Q 38 25 35 45 Z" fill="{hair}" stroke="{darken_color(hair, 0.7)}" stroke-width="1"/>'
    elif style == "long":
        hair_path = f'<path d="M 28 52 Q 28 20 60 16 Q 92 20 92 52 L 92 80 Q 90 85 86 80 L 86 50 Q 84 25 60 22 Q 36 25 34 50 L 34 80 Q 30 85 28 80 Z" fill="{hair}" stroke="{darken_color(hair, 0.7)}" stroke-width="1"/>'
    elif style == "spiky":
        hair_path = f'<path d="M 30 52 L 25 30 L 38 40 L 35 18 L 50 35 L 55 12 L 60 35 L 68 12 L 72 35 L 82 18 L 80 40 L 95 30 L 90 52 Q 88 25 60 20 Q 32 25 30 52 Z" fill="{hair}" stroke="{darken_color(hair, 0.7)}" stroke-width="1"/>'
    elif style == "bob":
        hair_path = f'<path d="M 30 55 Q 28 20 60 16 Q 92 20 90 55 Q 88 65 82 60 L 82 48 Q 80 28 60 22 Q 40 28 38 48 L 38 60 Q 32 65 30 55 Z" fill="{hair}" stroke="{darken_color(hair, 0.7)}" stroke-width="1"/>'
    else:  # ponytail
        hair_path = f'''<path d="M 30 52 Q 30 22 60 18 Q 90 22 90 52 L 85 45 Q 82 25 60 22 Q 38 25 35 45 Z" fill="{hair}" stroke="{darken_color(hair, 0.7)}" stroke-width="1"/>
    <path d="M 85 40 Q 95 35 98 50 Q 100 70 92 85 Q 88 90 85 82 Q 90 65 88 50 Z" fill="{hair}" stroke="{darken_color(hair, 0.7)}" stroke-width="1"/>'''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <!-- Background circle -->
  <circle cx="60" cy="60" r="58" fill="#F5F5F5" stroke="#E0E0E0" stroke-width="2"/>
  <!-- Neck -->
  <rect x="52" y="85" width="16" height="15" rx="3" fill="{skin}"/>
  <!-- Shirt -->
  <path d="M 35 100 Q 38 90 52 92 L 68 92 Q 82 90 85 100 L 85 118 L 35 118 Z" fill="{hair_colors[(char_id + 3) % len(hair_colors)]}" stroke="{darken_color(hair_colors[(char_id + 3) % len(hair_colors)], 0.7)}" stroke-width="1"/>
  <!-- Face -->
  <ellipse cx="60" cy="55" rx="30" ry="34" fill="{skin}" stroke="{dark_skin}" stroke-width="1"/>
  <!-- Hair -->
  {hair_path}
  <!-- Left eye -->
  <ellipse cx="48" cy="55" rx="4" ry="4.5" fill="#212121"/>
  <ellipse cx="49.5" cy="53.5" rx="1.5" ry="1.5" fill="white"/>
  <!-- Right eye -->
  <ellipse cx="72" cy="55" rx="4" ry="4.5" fill="#212121"/>
  <ellipse cx="73.5" cy="53.5" rx="1.5" ry="1.5" fill="white"/>
  <!-- Nose -->
  <path d="M 59 60 Q 60 64 62 60" fill="none" stroke="{dark_skin}" stroke-width="1" stroke-linecap="round"/>
  <!-- Mouth (smile) -->
  <path d="M 52 70 Q 60 77 68 70" fill="none" stroke="{darken_color(skin, 0.6)}" stroke-width="1.8" stroke-linecap="round"/>
  <!-- Cheek blush -->
  <ellipse cx="38" cy="65" rx="5" ry="3" fill="#FFCDD2" opacity="0.5"/>
  <ellipse cx="82" cy="65" rx="5" ry="3" fill="#FFCDD2" opacity="0.5"/>
</svg>'''
    return svg


def generate_other_svg(color_hex, char_id, race):
    """Generate SVG for Other/Special race characters."""
    body_color = color_hex
    dark_color = darken_color(color_hex, 0.6)
    light_color = lighten_color(color_hex, 0.35)
    accent = darken_color(color_hex, 0.45)

    # Different shapes based on race
    if race in ("Angol",):
        # Angol: ethereal, cosmic look with halo
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <defs>
    <radialGradient id="glow{char_id}" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{light_color}" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="{body_color}" stop-opacity="0.3"/>
    </radialGradient>
  </defs>
  <circle cx="60" cy="60" r="58" fill="#1A1A2E" stroke="{body_color}" stroke-width="2"/>
  <!-- Glow aura -->
  <circle cx="60" cy="60" r="45" fill="url(#glow{char_id})"/>
  <!-- Halo -->
  <ellipse cx="60" cy="25" rx="20" ry="6" fill="none" stroke="#FFD700" stroke-width="2.5" opacity="0.8"/>
  <!-- Face -->
  <circle cx="60" cy="58" r="28" fill="{lighten_color(body_color, 0.5)}" stroke="{dark_color}" stroke-width="1.5"/>
  <!-- Eyes -->
  <ellipse cx="50" cy="55" rx="5" ry="6" fill="white" stroke="{dark_color}" stroke-width="0.8"/>
  <ellipse cx="70" cy="55" rx="5" ry="6" fill="white" stroke="{dark_color}" stroke-width="0.8"/>
  <circle cx="51" cy="55" r="3" fill="{accent}"/>
  <circle cx="71" cy="55" r="3" fill="{accent}"/>
  <circle cx="52" cy="53.5" r="1.2" fill="white"/>
  <circle cx="72" cy="53.5" r="1.2" fill="white"/>
  <!-- Smile -->
  <path d="M 52 67 Q 60 73 68 67" fill="none" stroke="{dark_color}" stroke-width="1.5" stroke-linecap="round"/>
  <!-- Cosmic sparkles -->
  <polygon points="{star_points(25, 20, 4, 2, 4)}" fill="#FFD700" opacity="0.6"/>
  <polygon points="{star_points(90, 30, 3, 1.5, 4)}" fill="#FFD700" opacity="0.5"/>
  <polygon points="{star_points(85, 90, 3.5, 1.5, 4)}" fill="#FFD700" opacity="0.4"/>
</svg>'''
    elif race == "Ancient Weapon":
        # Mechanical/weapon look
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <circle cx="60" cy="60" r="58" fill="#263238" stroke="{body_color}" stroke-width="2"/>
  <!-- Mechanical body -->
  <circle cx="60" cy="60" r="35" fill="{body_color}" stroke="{dark_color}" stroke-width="2"/>
  <circle cx="60" cy="60" r="28" fill="{dark_color}" stroke="{accent}" stroke-width="1.5"/>
  <!-- Eye/sensor -->
  <circle cx="60" cy="55" r="12" fill="#F44336" opacity="0.9"/>
  <circle cx="60" cy="55" r="7" fill="#FF8A80"/>
  <circle cx="60" cy="55" r="3" fill="white"/>
  <!-- Gear teeth -->
  <rect x="57" y="22" width="6" height="8" rx="1" fill="{body_color}"/>
  <rect x="57" y="90" width="6" height="8" rx="1" fill="{body_color}"/>
  <rect x="22" y="57" width="8" height="6" rx="1" fill="{body_color}"/>
  <rect x="90" y="57" width="8" height="6" rx="1" fill="{body_color}"/>
  <!-- Bolts -->
  <circle cx="40" cy="40" r="3" fill="{accent}" stroke="{dark_color}" stroke-width="1"/>
  <circle cx="80" cy="40" r="3" fill="{accent}" stroke="{dark_color}" stroke-width="1"/>
  <circle cx="40" cy="80" r="3" fill="{accent}" stroke="{dark_color}" stroke-width="1"/>
  <circle cx="80" cy="80" r="3" fill="{accent}" stroke="{dark_color}" stroke-width="1"/>
</svg>'''
    elif race == "Robot":
        # Robot/mecha look
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <circle cx="60" cy="60" r="58" fill="#E8F5E9" stroke="{body_color}" stroke-width="2"/>
  <!-- Robot head -->
  <rect x="30" y="28" width="60" height="55" rx="10" fill="{body_color}" stroke="{dark_color}" stroke-width="2"/>
  <!-- Antenna -->
  <line x1="60" y1="28" x2="60" y2="15" stroke="{dark_color}" stroke-width="2"/>
  <circle cx="60" cy="12" r="4" fill="#F44336"/>
  <!-- Visor -->
  <rect x="36" y="42" width="48" height="18" rx="9" fill="{dark_color}"/>
  <!-- Eyes in visor -->
  <circle cx="48" cy="51" r="5" fill="#69F0AE"/>
  <circle cx="72" cy="51" r="5" fill="#69F0AE"/>
  <circle cx="49" cy="49.5" r="2" fill="white"/>
  <circle cx="73" cy="49.5" r="2" fill="white"/>
  <!-- Mouth plate -->
  <rect x="44" y="68" width="32" height="6" rx="3" fill="{dark_color}"/>
  <line x1="52" y1="68" x2="52" y2="74" stroke="{body_color}" stroke-width="1"/>
  <line x1="60" y1="68" x2="60" y2="74" stroke="{body_color}" stroke-width="1"/>
  <line x1="68" y1="68" x2="68" y2="74" stroke="{body_color}" stroke-width="1"/>
  <!-- Body -->
  <rect x="38" y="85" width="44" height="25" rx="5" fill="{body_color}" stroke="{dark_color}" stroke-width="1.5"/>
  <!-- Keron star on chest -->
  <polygon points="{star_points(60, 96, 8, 3.5, 5)}" fill="{darken_color(body_color, 0.5)}" stroke="{dark_color}" stroke-width="0.8"/>
</svg>'''
    elif race == "Spirit":
        # Ethereal/spirit look
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <defs>
    <radialGradient id="spirit{char_id}" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="white" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="{body_color}" stop-opacity="0.4"/>
    </radialGradient>
  </defs>
  <circle cx="60" cy="60" r="58" fill="#E0F7FA" stroke="{body_color}" stroke-width="2"/>
  <!-- Spirit body (wavy bottom) -->
  <path d="M 30 50 Q 30 25 60 20 Q 90 25 90 50 L 90 75 Q 85 85 78 75 Q 72 85 65 75 Q 58 85 52 75 Q 45 85 38 75 Q 32 85 30 75 Z" fill="url(#spirit{char_id})" stroke="{body_color}" stroke-width="1.5" opacity="0.85"/>
  <!-- Eyes -->
  <ellipse cx="48" cy="45" rx="6" ry="7" fill="white" stroke="{dark_color}" stroke-width="0.8"/>
  <ellipse cx="72" cy="45" rx="6" ry="7" fill="white" stroke="{dark_color}" stroke-width="0.8"/>
  <ellipse cx="49" cy="46" rx="3.5" ry="4.5" fill="{body_color}"/>
  <ellipse cx="73" cy="46" rx="3.5" ry="4.5" fill="{body_color}"/>
  <circle cx="50" cy="44" r="1.5" fill="white"/>
  <circle cx="74" cy="44" r="1.5" fill="white"/>
  <!-- Gentle smile -->
  <path d="M 52 58 Q 60 64 68 58" fill="none" stroke="{dark_color}" stroke-width="1.5" stroke-linecap="round"/>
  <!-- Sparkles -->
  <circle cx="35" cy="30" r="2" fill="white" opacity="0.7"/>
  <circle cx="85" cy="35" r="1.5" fill="white" opacity="0.6"/>
  <circle cx="25" cy="65" r="1.8" fill="white" opacity="0.5"/>
</svg>'''
    elif race == "Animal":
        # Cat (for Giroro's cat)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <circle cx="60" cy="60" r="58" fill="#FFF8E1" stroke="#FFE082" stroke-width="2"/>
  <!-- Cat ears -->
  <polygon points="28,35 38,10 50,40" fill="{body_color}" stroke="{dark_color}" stroke-width="1.5"/>
  <polygon points="70,40 82,10 92,35" fill="{body_color}" stroke="{dark_color}" stroke-width="1.5"/>
  <polygon points="32,35 40,18 48,40" fill="#FFCDD2"/>
  <polygon points="72,40 80,18 88,35" fill="#FFCDD2"/>
  <!-- Head -->
  <ellipse cx="60" cy="58" rx="34" ry="30" fill="{body_color}" stroke="{dark_color}" stroke-width="1.5"/>
  <!-- Calico patches -->
  <ellipse cx="42" cy="50" rx="12" ry="10" fill="#FF8A65" opacity="0.6"/>
  <ellipse cx="75" cy="62" rx="10" ry="8" fill="#212121" opacity="0.3"/>
  <!-- Eyes -->
  <ellipse cx="46" cy="55" rx="6" ry="7" fill="#FFF9C4"/>
  <ellipse cx="74" cy="55" rx="6" ry="7" fill="#FFF9C4"/>
  <ellipse cx="46" cy="56" rx="2.5" ry="5" fill="#212121"/>
  <ellipse cx="74" cy="56" rx="2.5" ry="5" fill="#212121"/>
  <!-- Nose -->
  <polygon points="58,64 62,64 60,67" fill="#F48FB1"/>
  <!-- Whiskers -->
  <line x1="20" y1="62" x2="42" y2="66" stroke="{dark_color}" stroke-width="0.8"/>
  <line x1="20" y1="68" x2="42" y2="68" stroke="{dark_color}" stroke-width="0.8"/>
  <line x1="78" y1="66" x2="100" y2="62" stroke="{dark_color}" stroke-width="0.8"/>
  <line x1="78" y1="68" x2="100" y2="68" stroke="{dark_color}" stroke-width="0.8"/>
  <!-- Mouth -->
  <path d="M 55 68 Q 60 73 65 68" fill="none" stroke="{dark_color}" stroke-width="1"/>
</svg>'''
    else:
        # Generic alien/Other
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <defs>
    <radialGradient id="alien{char_id}" cx="50%" cy="40%" r="55%">
      <stop offset="0%" stop-color="{light_color}"/>
      <stop offset="100%" stop-color="{body_color}"/>
    </radialGradient>
  </defs>
  <circle cx="60" cy="60" r="58" fill="#E8EAF6" stroke="{body_color}" stroke-width="2"/>
  <!-- Alien head (taller oval) -->
  <ellipse cx="60" cy="55" rx="32" ry="40" fill="url(#alien{char_id})" stroke="{dark_color}" stroke-width="1.5"/>
  <!-- Large eyes -->
  <ellipse cx="45" cy="50" rx="10" ry="12" fill="white" stroke="{dark_color}" stroke-width="1"/>
  <ellipse cx="75" cy="50" rx="10" ry="12" fill="white" stroke="{dark_color}" stroke-width="1"/>
  <ellipse cx="47" cy="51" rx="5" ry="7" fill="{accent}"/>
  <ellipse cx="77" cy="51" rx="5" ry="7" fill="{accent}"/>
  <circle cx="48" cy="48" r="2.5" fill="white"/>
  <circle cx="78" cy="48" r="2.5" fill="white"/>
  <!-- Small nose dots -->
  <circle cx="58" cy="65" r="1.5" fill="{dark_color}"/>
  <circle cx="62" cy="65" r="1.5" fill="{dark_color}"/>
  <!-- Smile -->
  <path d="M 50 72 Q 60 80 70 72" fill="none" stroke="{dark_color}" stroke-width="1.5" stroke-linecap="round"/>
  <!-- Star accent -->
  <polygon points="{star_points(60, 100, 7, 3, 5)}" fill="{accent}" opacity="0.6"/>
</svg>'''
    return svg


def sanitize_filename(name):
    """Create a safe filename from character name."""
    # Replace spaces and special chars
    safe = name.lower().strip()
    safe = re.sub(r"[^a-z0-9]", "_", safe)
    safe = re.sub(r"_+", "_", safe)
    safe = safe.strip("_")
    return safe


def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

    # Read characters
    with open(CHARACTERS_JSON, "r", encoding="utf-8") as f:
        characters = json.load(f)

    print(f"Loaded {len(characters)} characters from characters.json")

    generated_count = 0
    updates = []  # (id, image_url) pairs

    for char in characters:
        char_id = char["id"]
        name = char["name"]
        race = char.get("race", "Other")
        color = char.get("color")
        color_hex = get_hex_color(color)

        # Generate filename
        safe_name = sanitize_filename(name)
        filename = f"{char_id}_{safe_name}.svg"
        filepath = os.path.join(OUTPUT_DIR, filename)
        image_url = f"/images/characters/{filename}"

        # Generate SVG based on race
        if race == "Keronian":
            svg_content = generate_keronian_svg(color_hex, char_id)
        elif race == "Human":
            svg_content = generate_human_svg(char_id, name)
        else:
            svg_content = generate_other_svg(color_hex, char_id, race)

        # Write SVG file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)

        # Update character data
        char["image_url"] = image_url
        updates.append((image_url, char_id))
        generated_count += 1
        print(f"  [{char_id:2d}/72] {name} ({race}, {color or 'no color'}) -> {filename}")

    # Write updated characters.json
    with open(CHARACTERS_JSON, "w", encoding="utf-8") as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)
    print(f"\nUpdated characters.json with {generated_count} image_url entries")

    # Update database
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for image_url, char_id in updates:
            cursor.execute(
                "UPDATE characters SET image_url = ? WHERE id = ?",
                (image_url, char_id)
            )
        conn.commit()
        updated_rows = conn.total_changes
        conn.close()
        print(f"Updated {updated_rows} rows in keroro.db")
    except Exception as e:
        print(f"Database update error: {e}")
        # Try to see what tables exist
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Available tables: {tables}")
            conn.close()
        except Exception as e2:
            print(f"Could not inspect database: {e2}")

    print(f"\nDone! Generated {generated_count} SVG avatars in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
