"""Colour helpers: hex ↔ HSL, naming, and a simple harmony score between two garments."""
from __future__ import annotations

import colorsys

# A compact palette the UI offers as swatches.  name -> hex
PALETTE = {
    "black": "#1a1a1a", "white": "#f5f5f0", "cream": "#f1e9d2", "grey": "#8a8a8a",
    "charcoal": "#3b3b3b", "beige": "#d6c3a5", "camel": "#b8865b", "brown": "#6b4a2e",
    "navy": "#1f2a44", "denim": "#4a6fa5", "sky blue": "#9ec5e8", "cobalt": "#2f4fd1",
    "sage": "#9caf88", "olive": "#6b7a3a", "forest": "#2f5d3a", "mint": "#b8e0d2",
    "burgundy": "#6e1f2b", "red": "#c62828", "coral": "#ef6f5b", "rust": "#b7472a",
    "mustard": "#d8a21b", "butter": "#f3e39a", "lilac": "#c8b6e2", "plum": "#5c2a5e",
    "blush": "#f0b7b5", "hot pink": "#e0457b", "chocolate": "#4a2c20", "silver": "#c0c0c0",
    "oxblood": "#4e1a22", "moss": "#4f5d2f", "aubergine": "#3b1f3f", "ink": "#1b1f2e", "terracotta": "#9c4a2f",
    "dusty rose": "#b98a8a", "ochre": "#b57b1a",
}

NEUTRALS = {"black", "white", "cream", "grey", "charcoal", "beige", "camel", "brown",
            "navy", "denim", "chocolate", "silver", "ink", "oxblood"}


def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r / 255, g / 255, b / 255


def hex_to_hsl(h: str) -> tuple[float, float, float]:
    """Returns (hue 0-360, saturation 0-1, lightness 0-1)."""
    r, g, b = hex_to_rgb(h)
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, ss, ll


def is_neutral(h: str) -> bool:
    _, s, l = hex_to_hsl(h)
    return s < 0.22 or l < 0.16 or l > 0.9


def nearest_name(h: str) -> str:
    """Closest palette name for a hex colour (RGB distance)."""
    r, g, b = hex_to_rgb(h)
    best, best_d = "grey", 9.0
    for name, ph in PALETTE.items():
        pr, pg, pb = hex_to_rgb(ph)
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < best_d:
            best, best_d = name, d
    return best


def hue_distance(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def pair_score(h1: str, h2: str) -> float:
    """0..1 — how well two colours sit together. Neutrals are easy; hues follow the colour wheel."""
    n1, n2 = is_neutral(h1), is_neutral(h2)
    if n1 and n2:
        _, _, l1 = hex_to_hsl(h1)
        _, _, l2 = hex_to_hsl(h2)
        return 0.9 if abs(l1 - l2) > 0.25 else 0.75   # contrast between neutrals reads better
    if n1 or n2:
        return 0.88
    a, _, _ = hex_to_hsl(h1)
    b, _, _ = hex_to_hsl(h2)
    d = hue_distance(a, b)
    if d <= 15:
        return 0.7      # tonal — fine but flat
    if d <= 45:
        return 0.85     # analogous
    if 150 <= d <= 210:
        return 0.8      # complementary
    if 100 <= d < 150:
        return 0.65     # triadic-ish
    return 0.45         # clashing


def harmony(colours: list[str]) -> float:
    """Average pairwise score across an outfit's colours (1.0 for a single colour)."""
    if len(colours) < 2:
        return 1.0
    scores = [pair_score(colours[i], colours[j])
              for i in range(len(colours)) for j in range(i + 1, len(colours))]
    return sum(scores) / len(scores)
