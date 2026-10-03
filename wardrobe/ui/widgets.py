"""Small reusable widgets and helpers shared by the views."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk
from PIL import Image

from ..images import render
from ..logic.colours import PALETTE
from ..models import Item

# ---- theme tokens ----
ACCENT = "#8a5a44"          # warm cocoa
ACCENT_HOVER = "#6f4736"
CARD = ("#ffffff", "#262626")
CARD_HOVER = ("#f6f1ea", "#2f2f2f")
MUTED = ("#6b6b6b", "#a0a0a0")
FONT = "Helvetica"


def h1(master, text, **kw):
    kw.setdefault("anchor", "w")
    return ctk.CTkLabel(master, text=text, font=ctk.CTkFont(FONT, 24, "bold"), **kw)


def h2(master, text, **kw):
    kw.setdefault("anchor", "w")
    return ctk.CTkLabel(master, text=text, font=ctk.CTkFont(FONT, 16, "bold"), **kw)


def muted(master, text, **kw):
    kw.setdefault("anchor", "w")
    return ctk.CTkLabel(master, text=text, text_color=MUTED, font=ctk.CTkFont(FONT, 12), **kw)


def accent_button(master, text, command=None, **kw):
    kw.setdefault("fg_color", ACCENT)
    kw.setdefault("hover_color", ACCENT_HOVER)
    return ctk.CTkButton(master, text=text, command=command, **kw)


def ghost_button(master, text, command=None, **kw):
    kw.setdefault("fg_color", "transparent")
    kw.setdefault("border_width", 1)
    kw.setdefault("border_color", MUTED)
    kw.setdefault("text_color", ("#222222", "#eeeeee"))
    return ctk.CTkButton(master, text=text, command=command, **kw)


# ---- image cache ----
_cache: dict[tuple[str, int], ctk.CTkImage] = {}


def item_image(item: Item, size: int = 140) -> ctk.CTkImage:
    key = (item.image_path or f"gen:{item.subtype}:{item.colour}:{item.pattern}", size)
    if key in _cache:
        return _cache[key]
    img = None
    if item.image_path and Path(item.image_path).exists():
        try:
            img = Image.open(item.image_path).convert("RGB")
            # centre-crop to square then fit
            w, h = img.size
            m = min(w, h)
            img = img.crop(((w - m) // 2, (h - m) // 2, (w - m) // 2 + m, (h - m) // 2 + m))
        except Exception:
            img = None
    if img is None:
        img = render(item.subtype or "t-shirt", item.colour, item.pattern, size)
    img = img.resize((size, size), Image.LANCZOS)
    ci = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    _cache[key] = ci
    return ci


def forget_image(item: Item) -> None:
    for k in [k for k in _cache if k[0] == item.image_path]:
        _cache.pop(k, None)


# ---- item card ----
class ItemCard(ctk.CTkFrame):
    def __init__(self, master, item: Item, on_click: Callable[[Item], None] | None = None,
                 size: int = 140, wears: int | None = None, selected: bool = False, **kw):
        super().__init__(master, fg_color=CARD, corner_radius=14,
                         border_width=2 if selected else 0, border_color=ACCENT, **kw)
        self.item = item
        self.on_click = on_click
        img = ctk.CTkLabel(self, text="", image=item_image(item, size))
        img.pack(padx=10, pady=(10, 4))
        name = ctk.CTkLabel(self, text=item.name, font=ctk.CTkFont(FONT, 13, "bold"),
                            wraplength=size, justify="center")
        name.pack(padx=8)
        bits = [item.subtype or item.category]
        if wears is not None:
            bits.append(f"worn {wears}×")
        if item.status == "laundry":
            bits.append("in laundry")
        sub = muted(self, " · ".join(bits), anchor="center")
        sub.pack(padx=8, pady=(0, 2))
        if item.favourite:
            ctk.CTkLabel(self, text="★", text_color=ACCENT, font=ctk.CTkFont(FONT, 14)).pack(pady=(0, 6))
        else:
            ctk.CTkLabel(self, text=" ", font=ctk.CTkFont(FONT, 14)).pack(pady=(0, 6))
        for w in (self, img, name, sub):
            w.bind("<Button-1>", self._clicked)
            w.bind("<Enter>", lambda e: self.configure(fg_color=CARD_HOVER))
            w.bind("<Leave>", lambda e: self.configure(fg_color=CARD))

    def _clicked(self, _e=None):
        if self.on_click:
            self.on_click(self.item)


class ColourPicker(ctk.CTkFrame):
    """A grid of palette swatches plus a free hex entry."""

    def __init__(self, master, value: str = "#808080", on_change: Callable[[str, str], None] | None = None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.value = value
        self.on_change = on_change
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(anchor="w")
        self._buttons: dict[str, ctk.CTkButton] = {}
        for k, (name, hexv) in enumerate(PALETTE.items()):
            b = ctk.CTkButton(grid, text="", width=26, height=26, corner_radius=13, fg_color=hexv,
                              hover_color=hexv, border_width=2,
                              border_color=ACCENT if hexv == value else hexv,
                              command=lambda n=name, h=hexv: self.set(h, n))
            b.grid(row=k // 14, column=k % 14, padx=2, pady=2)
            self._buttons[hexv] = b
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="w", pady=(6, 0))
        muted(row, "or hex:").pack(side="left", padx=(0, 6))
        self.entry = ctk.CTkEntry(row, width=100)
        self.entry.insert(0, value)
        self.entry.pack(side="left")
        self.entry.bind("<FocusOut>", self._from_entry)
        self.entry.bind("<Return>", self._from_entry)
        self.swatch = ctk.CTkLabel(row, text="", width=26, height=26, corner_radius=13, fg_color=value)
        self.swatch.pack(side="left", padx=8)

    def set(self, hexv: str, name: str | None = None):
        from ..logic.colours import nearest_name
        self.value = hexv
        name = name or nearest_name(hexv)
        for h, b in self._buttons.items():
            b.configure(border_color=ACCENT if h == hexv else h)
        self.entry.delete(0, "end")
        self.entry.insert(0, hexv)
        self.swatch.configure(fg_color=hexv)
        if self.on_change:
            self.on_change(hexv, name)

    def _from_entry(self, _e=None):
        v = self.entry.get().strip()
        if not v.startswith("#"):
            v = "#" + v
        if len(v) in (4, 7):
            try:
                int(v[1:], 16)
                self.set(v)
            except ValueError:
                pass


class Toast:
    """Transient status message at the bottom of a frame."""

    def __init__(self, master):
        self.label = ctk.CTkLabel(master, text="", text_color=MUTED, font=ctk.CTkFont(FONT, 12))
        self.label.pack(side="bottom", anchor="w", padx=20, pady=(0, 8))
        self._job = None

    def show(self, text: str, ms: int = 3000):
        self.label.configure(text=text)
        if self._job:
            self.label.after_cancel(self._job)
        self._job = self.label.after(ms, lambda: self.label.configure(text=""))
