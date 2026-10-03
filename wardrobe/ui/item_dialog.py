"""Add / edit an item."""
from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

import customtkinter as ctk

from .. import USER_IMAGE_DIR
from ..images import placeholder_path
from ..logic.colours import PALETTE
from ..models import CATEGORIES, PATTERNS, SEASONS, SUBTYPES, Item
from .widgets import ACCENT, ColourPicker, accent_button, forget_image, ghost_button, h1, item_image, muted


class ItemDialog(ctk.CTkToplevel):
    def __init__(self, master, item: Item | None, on_save: Callable[[Item], None],
                 on_delete: Callable[[Item], None] | None = None):
        super().__init__(master)
        self.title("Edit item" if item else "Add item")
        self.geometry("760x680")
        self.resizable(False, True)
        self.on_save, self.on_delete = on_save, on_delete
        self.item = item or Item(name="", category="top", subtype="t-shirt", colour=PALETTE["black"],
                                 colour_name="black")
        self.new_image: str | None = None
        self._build()
        self.after(50, self.lift)
        self.grab_set()

    # ---------- layout ----------
    def _build(self):
        it = self.item
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(12, 0))
        h1(body, "Edit item" if it.id else "New item").pack(anchor="w", pady=(0, 8))

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        # image column
        imgcol = ctk.CTkFrame(top, fg_color="transparent")
        imgcol.pack(side="left", padx=(0, 16))
        self.img_label = ctk.CTkLabel(imgcol, text="", image=item_image(it, 180))
        self.img_label.pack()
        ghost_button(imgcol, "Choose photo…", command=self._choose_photo, width=160).pack(pady=(8, 4))
        muted(imgcol, "Placeholder until you add one", anchor="center").pack()

        # fields column
        f = ctk.CTkFrame(top, fg_color="transparent")
        f.pack(side="left", fill="both", expand=True)
        f.grid_columnconfigure(1, weight=1)

        def row(r, label, widget):
            muted(f, label).grid(row=r, column=0, sticky="w", padx=(0, 10), pady=4)
            widget.grid(row=r, column=1, sticky="ew", pady=4)
            return widget

        self.name = row(0, "Name", ctk.CTkEntry(f, placeholder_text="e.g. Camel wool coat"))
        self.name.insert(0, it.name)
        self.category = row(1, "Category", ctk.CTkOptionMenu(f, values=CATEGORIES, command=self._category_changed))
        self.category.set(it.category)
        self.subtype = row(2, "Type", ctk.CTkOptionMenu(f, values=SUBTYPES[it.category], command=lambda _: self._refresh_preview()))
        self.subtype.set(it.subtype or SUBTYPES[it.category][0])
        self.pattern = row(3, "Pattern", ctk.CTkOptionMenu(f, values=PATTERNS, command=lambda _: self._refresh_preview()))
        self.pattern.set(it.pattern)
        self.brand = row(4, "Brand", ctk.CTkEntry(f))
        self.brand.insert(0, it.brand)
        self.price = row(5, "Price (£)", ctk.CTkEntry(f, width=100))
        self.price.insert(0, f"{it.price:g}" if it.price else "")
        self.purchased = row(6, "Bought (YYYY-MM-DD)", ctk.CTkEntry(f, width=140))
        self.purchased.insert(0, it.purchased.isoformat() if it.purchased else "")
        self.tags = row(7, "Tags (comma separated)", ctk.CTkEntry(f, placeholder_text="basic, work, gym"))
        self.tags.insert(0, ", ".join(it.tags))

        # sliders
        sl = ctk.CTkFrame(body, fg_color="transparent")
        sl.pack(fill="x", pady=(10, 0))
        sl.grid_columnconfigure(1, weight=1)
        muted(sl, "Formality").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.formality = ctk.CTkSlider(sl, from_=1, to=5, number_of_steps=4, button_color=ACCENT, progress_color=ACCENT)
        self.formality.set(it.formality)
        self.formality.grid(row=0, column=1, sticky="ew")
        self.formality_lbl = muted(sl, "", width=150)
        self.formality_lbl.grid(row=0, column=2, padx=8)
        muted(sl, "Warmth").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(6, 0))
        self.warmth = ctk.CTkSlider(sl, from_=1, to=5, number_of_steps=4, button_color=ACCENT, progress_color=ACCENT)
        self.warmth.set(it.warmth)
        self.warmth.grid(row=1, column=1, sticky="ew", pady=(6, 0))
        self.warmth_lbl = muted(sl, "", width=150)
        self.warmth_lbl.grid(row=1, column=2, padx=8, pady=(6, 0))
        self.formality.configure(command=lambda v: self._slider_labels())
        self.warmth.configure(command=lambda v: self._slider_labels())
        self._slider_labels()

        # seasons + flags
        sf = ctk.CTkFrame(body, fg_color="transparent")
        sf.pack(fill="x", pady=(10, 0))
        muted(sf, "Seasons").pack(side="left", padx=(0, 10))
        self.season_vars = {}
        for s in SEASONS:
            v = ctk.BooleanVar(value=s in it.seasons)
            ctk.CTkCheckBox(sf, text=s, variable=v, fg_color=ACCENT, hover_color=ACCENT, width=90).pack(side="left")
            self.season_vars[s] = v
        self.fav = ctk.BooleanVar(value=it.favourite)
        ctk.CTkCheckBox(sf, text="★ favourite", variable=self.fav, fg_color=ACCENT, hover_color=ACCENT).pack(side="left", padx=(16, 0))
        self.laundry = ctk.BooleanVar(value=it.status == "laundry")
        ctk.CTkCheckBox(sf, text="in laundry", variable=self.laundry, fg_color=ACCENT, hover_color=ACCENT).pack(side="left", padx=(16, 0))

        # colour
        muted(body, "Colour").pack(anchor="w", pady=(12, 2))
        self.colour = ColourPicker(body, it.colour, on_change=self._colour_changed)
        self.colour.pack(anchor="w")
        self.colour_name = it.colour_name

        muted(body, "Notes").pack(anchor="w", pady=(12, 2))
        self.notes = ctk.CTkTextbox(body, height=60)
        self.notes.insert("1.0", it.notes)
        self.notes.pack(fill="x")

        # buttons
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=16, pady=12)
        accent_button(bar, "Save", command=self._save, width=120).pack(side="right")
        ghost_button(bar, "Cancel", command=self.destroy, width=100).pack(side="right", padx=8)
        if it.id and self.on_delete:
            ghost_button(bar, "Delete", command=self._delete, width=100, border_color="#c0392b",
                         text_color="#c0392b").pack(side="left")

    # ---------- behaviour ----------
    def _slider_labels(self):
        f = int(round(self.formality.get()))
        w = int(round(self.warmth.get()))
        self.formality_lbl.configure(text=["", "lounge", "casual", "smart-casual", "smart", "formal"][f])
        self.warmth_lbl.configure(text=["", "summer", "light", "mid", "warm", "winter"][w])

    def _category_changed(self, cat: str):
        self.subtype.configure(values=SUBTYPES[cat])
        self.subtype.set(SUBTYPES[cat][0])
        self._refresh_preview()

    def _colour_changed(self, hexv: str, name: str):
        self.colour_name = name
        self._refresh_preview()

    def _refresh_preview(self):
        if self.new_image or (self.item.image_path and "placeholders" not in self.item.image_path
                              and Path(self.item.image_path).exists()):
            return   # real photo — keep it
        preview = Item(name="", category=self.category.get(), subtype=self.subtype.get(),
                       colour=self.colour.value, pattern=self.pattern.get())
        self.img_label.configure(image=item_image(preview, 180))

    def _choose_photo(self):
        p = filedialog.askopenfilename(title="Choose a photo",
                                       filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.heic"), ("All", "*.*")])
        if not p:
            return
        USER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        dest = USER_IMAGE_DIR / f"{date.today().isoformat()}_{Path(p).name}"
        try:
            shutil.copy2(p, dest)
        except OSError as e:
            messagebox.showerror("Couldn't copy photo", str(e), parent=self)
            return
        self.new_image = str(dest)
        tmp = Item(name="", category=self.category.get(), subtype=self.subtype.get(), image_path=self.new_image)
        self.img_label.configure(image=item_image(tmp, 180))

    def _save(self):
        it = self.item
        name = self.name.get().strip()
        if not name:
            messagebox.showwarning("Name needed", "Give the item a name.", parent=self)
            return
        it.name = name
        it.category = self.category.get()
        it.subtype = self.subtype.get()
        it.pattern = self.pattern.get()
        it.brand = self.brand.get().strip()
        try:
            it.price = float(self.price.get().replace("£", "").strip() or 0)
        except ValueError:
            messagebox.showwarning("Price", "Price should be a number.", parent=self)
            return
        p = self.purchased.get().strip()
        try:
            it.purchased = date.fromisoformat(p) if p else None
        except ValueError:
            messagebox.showwarning("Date", "Use YYYY-MM-DD for the purchase date.", parent=self)
            return
        it.tags = [t.strip().lower() for t in self.tags.get().split(",") if t.strip()]
        it.formality = int(round(self.formality.get()))
        it.warmth = int(round(self.warmth.get()))
        it.seasons = [s for s, v in self.season_vars.items() if v.get()] or list(SEASONS)
        it.favourite = self.fav.get()
        it.status = "laundry" if self.laundry.get() else "clean"
        it.colour = self.colour.value
        it.colour_name = self.colour_name
        it.notes = self.notes.get("1.0", "end").strip()
        if self.new_image:
            it.image_path = self.new_image
        elif not it.image_path or "placeholders" in it.image_path:
            it.image_path = str(placeholder_path(it.subtype, it.colour, it.pattern))
        forget_image(it)
        self.on_save(it)
        self.destroy()

    def _delete(self):
        if messagebox.askyesno("Delete", f"Delete “{self.item.name}” from your wardrobe?", parent=self):
            self.on_delete(self.item)
            self.destroy()
