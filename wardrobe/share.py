"""Compose an outfit into a single shareable PNG (flat-lay collage with a caption)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .images import render
from .models import Item

BG = (250, 247, 242)
INK = (40, 36, 32)
MUTED = (120, 112, 104)


def _font(size: int):
    for name in ("DejaVuSans.ttf", "Helvetica.ttc", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _tile(item: Item, size: int) -> Image.Image:
    if item.image_path and Path(item.image_path).exists():
        try:
            im = Image.open(item.image_path).convert("RGB")
            w, h = im.size
            m = min(w, h)
            im = im.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m))
            return im.resize((size, size), Image.LANCZOS)
        except Exception:
            pass
    return render(item.subtype or "t-shirt", item.colour, item.pattern, size)


def outfit_image(items: list[Item], title: str, subtitle: str = "", tile: int = 300) -> Image.Image:
    n = max(1, len(items))
    cols = min(n, 3)
    rows = (n + cols - 1) // cols
    pad, gap, head = 40, 20, 110
    w = pad * 2 + cols * tile + (cols - 1) * gap
    h = head + pad + rows * (tile + 34) + (rows - 1) * gap
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    d.text((pad, 34), title, fill=INK, font=_font(34))
    if subtitle:
        d.text((pad, 78), subtitle, fill=MUTED, font=_font(18))
    for k, it in enumerate(items):
        x = pad + (k % cols) * (tile + gap)
        y = head + pad + (k // cols) * (tile + 34 + gap)
        img.paste(_tile(it, tile), (x, y))
        d.text((x, y + tile + 8), it.name[:28], fill=INK, font=_font(16))
    return img


def save_outfit_image(items: list[Item], title: str, path: Path | str, subtitle: str = "") -> Path:
    p = Path(path)
    outfit_image(items, title, subtitle).save(p)
    return p
