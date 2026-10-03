"""Placeholder garment illustrations drawn with Pillow.

Until you photograph your real clothes, every item gets a clean flat-lay style
silhouette in its own colour.  `render(subtype, colour, pattern)` returns a PIL image;
`placeholder_path(...)` caches it on disk and returns the path.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from . import PLACEHOLDER_DIR

SIZE = 512
BG = (247, 244, 239)        # warm off-white card
SHADOW = (0, 0, 0, 38)


def _shade(hex_colour: str, k: float) -> tuple[int, int, int]:
    h = hex_colour.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return tuple(max(0, min(255, int(c * k))) for c in (r, g, b))


def _rgb(hex_colour: str) -> tuple[int, int, int]:
    return _shade(hex_colour, 1.0)


# ---------- silhouettes (coordinates in a 0..100 box) ----------
def _tee():
    return [(22, 18), (38, 12), (44, 20), (56, 20), (62, 12), (78, 18), (88, 34), (74, 42),
            (74, 90), (26, 90), (26, 42), (12, 34)]


def _shirt():
    return [(20, 16), (40, 10), (50, 22), (60, 10), (80, 16), (92, 36), (76, 42),
            (76, 92), (24, 92), (24, 42), (8, 36)]


def _jumper():
    return [(18, 18), (38, 12), (50, 18), (62, 12), (82, 18), (94, 50), (80, 54),
            (80, 90), (20, 90), (20, 54), (6, 50)]


def _tank():
    return [(32, 12), (40, 12), (44, 30), (56, 30), (60, 12), (68, 12), (72, 36),
            (72, 92), (28, 92), (28, 36)]


def _trousers():
    return [(28, 8), (72, 8), (76, 50), (74, 94), (54, 94), (50, 48), (46, 94), (26, 94), (24, 50)]


def _shorts():
    return [(28, 8), (72, 8), (78, 52), (54, 52), (50, 36), (46, 52), (22, 52)]


def _skirt():
    return [(34, 10), (66, 10), (84, 90), (16, 90)]


def _dress():
    return [(32, 8), (42, 8), (46, 20), (54, 20), (58, 8), (68, 8), (72, 36), (64, 42),
            (86, 94), (14, 94), (36, 42), (28, 36)]


def _coat():
    return [(16, 14), (38, 8), (50, 20), (62, 8), (84, 14), (96, 40), (82, 46),
            (86, 96), (14, 96), (18, 46), (4, 40)]


def _blazer():
    return [(18, 14), (40, 8), (50, 26), (60, 8), (82, 14), (92, 40), (78, 46),
            (78, 92), (22, 92), (22, 46), (8, 40)]


def _sneaker():
    return [(6, 58), (14, 44), (30, 36), (46, 34), (60, 40), (74, 50), (92, 56), (96, 68),
            (94, 76), (6, 76)]


def _boot():
    return [(30, 8), (62, 8), (62, 60), (92, 66), (92, 80), (28, 80), (28, 60)]


def _heel():
    return [(6, 66), (20, 56), (44, 40), (62, 34), (80, 34), (94, 40), (94, 50), (80, 52),
            (68, 60), (60, 72), (60, 86), (50, 86), (50, 72), (40, 72), (28, 74), (6, 74)]


def _sandal():
    return [(12, 60), (40, 46), (70, 48), (92, 60), (92, 72), (12, 74)]


def _tote():
    return [(20, 36), (80, 36), (86, 92), (14, 92)]


def _crossbody():
    return [(22, 44), (78, 44), (82, 86), (18, 86)]


def _backpack():
    return [(26, 24), (74, 24), (80, 90), (20, 90)]


def _scarf():
    return [(30, 6), (46, 6), (54, 60), (70, 94), (56, 94), (48, 70), (40, 94), (26, 94), (42, 60)]


def _hat():
    return [(6, 62), (30, 60), (34, 30), (42, 22), (58, 22), (66, 30), (70, 60), (94, 62),
            (94, 70), (6, 70)]


def _sunglasses():
    return [(4, 40), (46, 38), (50, 44), (54, 38), (96, 40), (94, 50), (86, 64), (62, 66), (54, 54),
            (46, 54), (38, 66), (14, 64), (6, 50)]


def _flares():
    return [(28, 8), (72, 8), (74, 50), (88, 94), (56, 94), (50, 50), (44, 94), (12, 94), (26, 50)]


def _maxi_skirt():
    return [(36, 6), (64, 6), (90, 96), (10, 96)]


def _corset():
    return [(26, 14), (42, 18), (50, 12), (58, 18), (74, 14), (72, 40), (70, 60), (76, 90), (24, 90),
            (30, 60), (28, 40)]


def _platform():
    return [(30, 6), (62, 6), (62, 56), (92, 62), (92, 86), (28, 86), (28, 56)]


def _maryjane():
    return [(6, 60), (14, 48), (34, 40), (56, 40), (78, 48), (94, 60), (94, 72), (6, 72)]


def _shoulder_bag():
    return [(16, 48), (84, 48), (80, 88), (20, 88)]


def _choker():
    return [(8, 46), (92, 46), (92, 56), (8, 56)]


def _generic():
    return [(20, 20), (80, 20), (80, 80), (20, 80)]


SHAPES = {
    "baby tee": _tee, "mesh top": _tee, "corset top": _corset, "flared jeans": _flares,
    "cargo trousers": _trousers, "maxi skirt": _maxi_skirt, "slip dress": _dress, "maxi dress": _dress,
    "long coat": _coat, "leather jacket": _blazer, "platform boots": _platform, "mary janes": _maryjane,
    "shoulder bag": _shoulder_bag, "choker": _choker, "tights": _trousers,
    "t-shirt": _tee, "tank": _tank, "shirt": _shirt, "blouse": _shirt, "turtleneck": _jumper,
    "jumper": _jumper, "hoodie": _jumper, "cardigan": _shirt,
    "jeans": _trousers, "trousers": _trousers, "leggings": _trousers, "joggers": _trousers,
    "shorts": _shorts, "skirt": _skirt,
    "dress": _dress, "jumpsuit": _dress, "abaya": _dress,
    "coat": _coat, "trench": _coat, "puffer": _coat, "jacket": _blazer, "blazer": _blazer,
    "denim jacket": _blazer,
    "sneakers": _sneaker, "boots": _boot, "heels": _heel, "loafers": _sneaker, "flats": _sneaker,
    "sandals": _sandal,
    "tote": _tote, "crossbody": _crossbody, "backpack": _backpack, "clutch": _crossbody,
    "scarf": _scarf, "hat": _hat, "belt": _hat, "jewellery": _generic, "sunglasses": _sunglasses,
    "hijab": _scarf,
}


def _scale(pts, box=(70, 50, 442, 462)):
    x0, y0, x1, y1 = box
    return [(x0 + px / 100 * (x1 - x0), y0 + py / 100 * (y1 - y0)) for px, py in pts]


def _pattern_layer(mask: Image.Image, pattern: str, base: tuple[int, int, int]) -> Image.Image:
    layer = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    dark = tuple(int(c * 0.72) for c in base) + (255,)
    light = tuple(min(255, int(c * 1.25) + 20) for c in base) + (255,)
    w, h = mask.size
    if pattern == "stripes":
        for y in range(0, h, 28):
            d.rectangle([0, y, w, y + 11], fill=light)
    elif pattern == "dots":
        for y in range(0, h, 40):
            for x in range(0, w, 40):
                off = 20 if (y // 40) % 2 else 0
                d.ellipse([x + off, y, x + off + 12, y + 12], fill=light)
    elif pattern == "check":
        for y in range(0, h, 44):
            d.rectangle([0, y, w, y + 16], fill=dark)
        for x in range(0, w, 44):
            d.rectangle([x, 0, x + 16, h], fill=dark)
    elif pattern == "floral":
        for y in range(10, h, 56):
            for x in range(10, w, 56):
                for dx, dy in ((0, -9), (9, 0), (0, 9), (-9, 0)):
                    d.ellipse([x + dx - 7, y + dy - 7, x + dx + 7, y + dy + 7], fill=light)
                d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=dark)
    elif pattern == "lace":
        for y in range(0, h, 18):
            for x in range(0, w, 18):
                d.ellipse([x + 2, y + 2, x + 14, y + 14], outline=light, width=2)
    elif pattern == "velvet":
        for y in range(0, h, 6):
            d.line([(0, y), (w, y)], fill=light if (y // 6) % 3 == 0 else dark, width=1)
    elif pattern == "leopard":
        import random as _r
        rr = _r.Random(3)
        for _ in range(140):
            x, y = rr.randint(0, w), rr.randint(0, h)
            d.ellipse([x - 9, y - 7, x + 9, y + 7], outline=dark, width=4)
            d.ellipse([x - 5, y - 3, x + 5, y + 3], fill=light)
    elif pattern == "graphic":
        d.rectangle([w * 0.33, h * 0.36, w * 0.67, h * 0.6], fill=light)
        d.rectangle([w * 0.38, h * 0.41, w * 0.62, h * 0.55], fill=dark)
    layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", mask.size, 0), mask))
    return layer


def render(subtype: str, colour: str = "#808080", pattern: str = "solid", size: int = SIZE) -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), BG + (255,))
    shape = SHAPES.get(subtype, _generic)()
    pts = _scale(shape)
    base = _rgb(colour)

    # soft drop shadow
    sh = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(sh).polygon([(x + 10, y + 14) for x, y in pts], fill=SHADOW)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(sh)

    # garment body
    body = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(body).polygon(pts, fill=base + (255,))
    img.alpha_composite(body)
    mask = body.getchannel("A")
    if pattern != "solid":
        img.alpha_composite(_pattern_layer(mask, pattern, base))

    # a few seams / details so shapes read as clothes (clipped to the garment)
    det = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    d = ImageDraw.Draw(det)
    seam = _shade(colour, 0.78) + (255,)
    light = tuple(min(255, int(c * 1.3) + 25) for c in base) + (255,)
    if subtype in ("t-shirt", "baby tee", "mesh top", "shirt", "blouse", "jumper", "hoodie", "turtleneck",
                   "cardigan", "tank"):
        d.arc([SIZE * 0.40, SIZE * 0.10, SIZE * 0.60, SIZE * 0.26], 0, 180, fill=seam, width=4)
    if subtype in ("shirt", "blouse", "cardigan", "coat", "long coat", "blazer", "jacket", "leather jacket",
                   "trench", "denim jacket"):
        d.line([(SIZE * 0.5, SIZE * 0.26), (SIZE * 0.5, SIZE * 0.9)], fill=seam, width=3)
        for k in range(4):
            y = SIZE * (0.36 + 0.13 * k)
            d.ellipse([SIZE * 0.5 - 6, y - 6, SIZE * 0.5 + 6, y + 6], fill=seam)
    if subtype == "cargo trousers":
        for cx in (0.3, 0.7):
            d.rectangle([SIZE * (cx - 0.08), SIZE * 0.42, SIZE * (cx + 0.08), SIZE * 0.56], outline=seam, width=3)
    if subtype == "corset top":
        for k in range(5):
            y = SIZE * (0.3 + 0.1 * k)
            d.line([(SIZE * 0.44, y), (SIZE * 0.56, y + 12)], fill=light, width=2)
            d.line([(SIZE * 0.56, y), (SIZE * 0.44, y + 12)], fill=light, width=2)
    if subtype == "mary janes":
        d.line([(SIZE * 0.3, SIZE * 0.42), (SIZE * 0.7, SIZE * 0.42)], fill=seam, width=5)
    if subtype == "platform boots":
        d.rectangle([0, SIZE * 0.72, SIZE, SIZE], fill=light)
        d.line([(0, SIZE * 0.72), (SIZE, SIZE * 0.72)], fill=seam, width=3)
        d.line([(0, SIZE * 0.82), (SIZE, SIZE * 0.82)], fill=seam, width=2)
    if subtype == "mesh top":
        for x in range(0, SIZE, 10):
            d.line([(x, 0), (x, SIZE)], fill=light, width=1)
        for y in range(0, SIZE, 10):
            d.line([(0, y), (SIZE, y)], fill=light, width=1)
    if subtype in ("jeans", "flared jeans", "cargo trousers", "trousers", "joggers", "leggings", "shorts", "tights"):
        d.line([(SIZE * 0.5, SIZE * 0.1), (SIZE * 0.5, SIZE * 0.44)], fill=seam, width=3)
        d.line([(0, SIZE * 0.175), (SIZE, SIZE * 0.175)], fill=seam, width=4)
    if subtype in ("jeans", "flared jeans"):
        d.line([(SIZE * 0.36, SIZE * 0.2), (SIZE * 0.33, SIZE * 0.9)], fill=light, width=2)
        d.line([(SIZE * 0.64, SIZE * 0.2), (SIZE * 0.67, SIZE * 0.9)], fill=light, width=2)
    if subtype in ("tote", "crossbody", "clutch", "backpack", "shoulder bag"):
        d.line([(0, SIZE * 0.3), (SIZE, SIZE * 0.3)], fill=seam, width=3)
    if subtype in ("sneakers", "loafers", "flats", "sandals"):
        d.rectangle([0, SIZE * 0.69, SIZE, SIZE], fill=light)          # sole
        d.line([(0, SIZE * 0.69), (SIZE, SIZE * 0.69)], fill=seam, width=3)
    if subtype == "sneakers":
        for k in range(4):
            x = SIZE * (0.36 + 0.07 * k)
            d.line([(x, SIZE * 0.42 - k * 6), (x + 14, SIZE * 0.5 - k * 6)], fill=light, width=4)
    if subtype == "boots":
        d.rectangle([0, SIZE * 0.78, SIZE, SIZE], fill=light)
        d.line([(0, SIZE * 0.78), (SIZE, SIZE * 0.78)], fill=seam, width=3)
    if subtype == "hat":
        d.line([(0, SIZE * 0.6), (SIZE, SIZE * 0.6)], fill=seam, width=6)
    det.putalpha(Image.composite(det.getchannel("A"), Image.new("L", (SIZE, SIZE), 0), mask))
    img.alpha_composite(det)
    # bag handles sit outside the body
    if subtype in ("tote", "crossbody", "clutch", "backpack", "shoulder bag"):
        ImageDraw.Draw(img).arc([SIZE * 0.3, SIZE * 0.06, SIZE * 0.7, SIZE * 0.42], 180, 360,
                                fill=_shade(colour, 0.78) + (255,), width=7)

    out = img.convert("RGB")
    if size != SIZE:
        out = out.resize((size, size), Image.LANCZOS)
    return out


def placeholder_path(subtype: str, colour: str, pattern: str = "solid") -> Path:
    """Render once, cache on disk, return the path (relative to nothing — absolute)."""
    PLACEHOLDER_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(f"{subtype}|{colour}|{pattern}".encode()).hexdigest()[:10]
    p = PLACEHOLDER_DIR / f"{subtype.replace(' ', '_')}_{key}.png"
    if not p.exists():
        render(subtype, colour, pattern).save(p)
    return p
