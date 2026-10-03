"""Outfits: generate suggestions, build one by hand, keep the ones you like, log wears."""
from __future__ import annotations

import random
from datetime import date
from tkinter import messagebox, simpledialog

import customtkinter as ctk

from ..logic.outfits import Suggestion, generate, outfit_name, score_outfit, season_for
from ..models import CATEGORIES, OCCASIONS, Item, Outfit
from .widgets import ACCENT, CARD, Toast, accent_button, ghost_button, h1, h2, item_image, muted

THUMB = 96


class OutfitStrip(ctk.CTkFrame):
    """A horizontal row of item thumbnails with a title, score and action buttons."""

    def __init__(self, master, items: list[Item], title: str, subtitle: str = "", actions=(), **kw):
        super().__init__(master, fg_color=CARD, corner_radius=14, **kw)
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=12, pady=(10, 0))
        h2(head, title).pack(side="left")
        for text, cmd in actions:
            ghost_button(head, text, command=cmd, width=90, height=28).pack(side="right", padx=4)
        if subtitle:
            muted(self, subtitle, wraplength=700).pack(anchor="w", padx=12)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=8)
        for it in items:
            cell = ctk.CTkFrame(row, fg_color="transparent")
            cell.pack(side="left", padx=4)
            ctk.CTkLabel(cell, text="", image=item_image(it, THUMB)).pack()
            muted(cell, it.name if len(it.name) < 18 else it.name[:16] + "…", anchor="center").pack()


class OutfitView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.repo = app.repo
        self.manual_sel: dict[str, Item | None] = {c: None for c in CATEGORIES}
        self._build()
        self.refresh()

    # ---------- layout ----------
    def _build(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(18, 6))
        h1(head, "Outfits").pack(side="left")

        self.tabs = ctk.CTkTabview(self, segmented_button_selected_color=ACCENT,
                                   segmented_button_selected_hover_color=ACCENT, fg_color="transparent")
        self.tabs.pack(fill="both", expand=True, padx=12)
        self.tab_gen = self.tabs.add("Suggest")
        self.tab_manual = self.tabs.add("Build by hand")
        self.tab_saved = self.tabs.add("Saved")
        self._build_generator(self.tab_gen)
        self._build_manual(self.tab_manual)
        self.saved_frame = ctk.CTkScrollableFrame(self.tab_saved, fg_color="transparent")
        self.saved_frame.pack(fill="both", expand=True)
        self.toast = Toast(self)

    def _build_generator(self, tab):
        ctrl = ctk.CTkFrame(tab, fg_color=CARD, corner_radius=14)
        ctrl.pack(fill="x", padx=8, pady=8)
        inner = ctk.CTkFrame(ctrl, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        muted(inner, "Occasion").pack(side="left")
        self.occasion = ctk.CTkOptionMenu(inner, values=OCCASIONS, width=110, fg_color=ACCENT, button_color=ACCENT)
        self.occasion.set("casual")
        self.occasion.pack(side="left", padx=(6, 16))
        muted(inner, "Temperature").pack(side="left")
        self.temp = ctk.CTkSlider(inner, from_=-5, to=32, number_of_steps=37, width=180,
                                  button_color=ACCENT, progress_color=ACCENT, command=self._temp_label)
        self.temp.set(14)
        self.temp.pack(side="left", padx=6)
        self.temp_lbl = muted(inner, "14°C", width=46)
        self.temp_lbl.pack(side="left")
        self.rain = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(inner, text="rain", variable=self.rain, fg_color=ACCENT, hover_color=ACCENT, width=70).pack(side="left", padx=(12, 0))
        muted(inner, "Season").pack(side="left", padx=(12, 0))
        self.season = ctk.CTkOptionMenu(inner, values=["auto", "spring", "summer", "autumn", "winter"], width=100,
                                        fg_color=ACCENT, button_color=ACCENT)
        self.season.set("auto")
        self.season.pack(side="left", padx=6)
        accent_button(inner, "Suggest outfits", command=self.suggest, width=140).pack(side="right")
        self.results = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.results.pack(fill="both", expand=True, padx=8)
        muted(self.results, "Pick an occasion and the weather, then hit Suggest.").pack(pady=30)

    def _build_manual(self, tab):
        top = ctk.CTkFrame(tab, fg_color=CARD, corner_radius=14)
        top.pack(fill="x", padx=8, pady=8)
        inner = ctk.CTkFrame(top, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)
        self.manual_menus: dict[str, ctk.CTkOptionMenu] = {}
        for c in CATEGORIES:
            col = ctk.CTkFrame(inner, fg_color="transparent")
            col.pack(side="left", padx=4)
            muted(col, c).pack(anchor="w")
            m = ctk.CTkOptionMenu(col, values=["—"], width=150, command=lambda v, cat=c: self._manual_pick(cat, v),
                                  fg_color=ACCENT, button_color=ACCENT)
            m.set("—")
            m.pack()
            self.manual_menus[c] = m
        bar = ctk.CTkFrame(top, fg_color="transparent")
        bar.pack(fill="x", padx=12, pady=(0, 10))
        muted(bar, "Score against:").pack(side="left")
        self.manual_occ = ctk.CTkOptionMenu(bar, values=OCCASIONS, width=100, fg_color=ACCENT, button_color=ACCENT,
                                            command=lambda _: self._manual_render())
        self.manual_occ.set("casual")
        self.manual_occ.pack(side="left", padx=6)
        ghost_button(bar, "Clear", command=self._manual_clear, width=80).pack(side="right")
        accent_button(bar, "Save outfit", command=self._manual_save, width=110).pack(side="right", padx=8)
        self.manual_preview = ctk.CTkFrame(tab, fg_color="transparent")
        self.manual_preview.pack(fill="both", expand=True, padx=8)

    # ---------- generator ----------
    def _temp_label(self, v):
        self.temp_lbl.configure(text=f"{int(round(float(v)))}°C")

    def suggest(self):
        for w in self.results.winfo_children():
            w.destroy()
        items = self.repo.items()
        season = None if self.season.get() == "auto" else self.season.get()
        sugs = generate(items, self.occasion.get(), float(self.temp.get()), self.rain.get(),
                        season=season, wear_counts=self.repo.wear_counts(), n=4, rng=random.Random())
        if not sugs:
            muted(self.results, "Nothing clean fits that — check seasons, formality tags and the laundry basket.").pack(pady=30)
            return
        for k, s in enumerate(sugs):
            self._suggestion_strip(s, k)

    def _suggestion_strip(self, s: Suggestion, k: int):
        occ = self.occasion.get()
        strip = OutfitStrip(self.results, s.items, f"Option {k + 1}  ·  {s.score:.0%}", ", ".join(s.reasons),
                            actions=[("Wear today", lambda s=s: self._wear(s.items, occ)),
                                     ("Save", lambda s=s: self._save_suggestion(s, occ))])
        strip.pack(fill="x", pady=6)

    def _save_suggestion(self, s: Suggestion, occ: str):
        name = simpledialog.askstring("Save outfit", "Name this outfit:", initialvalue=outfit_name(s.items, occ), parent=self)
        if not name:
            return
        self.repo.add_outfit(Outfit(name=name, item_ids=s.item_ids, occasion=occ, score=s.score))
        self.toast.show(f"Saved “{name}”")
        self.refresh()

    def _wear(self, items: list[Item], occ: str, outfit_id: int | None = None):
        self.repo.log_wear([i.id for i in items], outfit_id=outfit_id)
        self.toast.show("Logged as worn today")
        self.app.data_changed()

    # ---------- manual ----------
    def _manual_options(self):
        self._by_cat = {c: self.repo.items(category=c) for c in CATEGORIES}
        for c, m in self.manual_menus.items():
            names = ["—"] + [i.name for i in self._by_cat[c]]
            m.configure(values=names)
            cur = self.manual_sel.get(c)
            m.set(cur.name if cur and cur.name in names else "—")

    def _manual_pick(self, cat: str, value: str):
        self.manual_sel[cat] = next((i for i in self._by_cat[cat] if i.name == value), None)
        self._manual_render()

    def _manual_items(self) -> list[Item]:
        return [i for i in self.manual_sel.values() if i]

    def _manual_render(self):
        for w in self.manual_preview.winfo_children():
            w.destroy()
        items = self._manual_items()
        if not items:
            muted(self.manual_preview, "Pick pieces above to see them together.").pack(pady=30)
            return
        sc, reasons = score_outfit(items, self.manual_occ.get(), 15, False, self.repo.wear_counts())
        OutfitStrip(self.manual_preview, items, f"Your combination  ·  {sc:.0%}", ", ".join(reasons),
                    actions=[("Wear today", lambda: self._wear(items, self.manual_occ.get()))]).pack(fill="x", pady=6)

    def _manual_clear(self):
        self.manual_sel = {c: None for c in CATEGORIES}
        self._manual_options()
        self._manual_render()

    def _manual_save(self):
        items = self._manual_items()
        if len(items) < 2:
            messagebox.showinfo("Outfit", "Pick at least two pieces.", parent=self)
            return
        occ = self.manual_occ.get()
        name = simpledialog.askstring("Save outfit", "Name this outfit:", initialvalue=outfit_name(items, occ), parent=self)
        if not name:
            return
        sc, _ = score_outfit(items, occ, 15, False)
        self.repo.add_outfit(Outfit(name=name, item_ids=[i.id for i in items], occasion=occ, score=sc))
        self.toast.show(f"Saved “{name}”")
        self.refresh()

    # ---------- saved ----------
    def refresh(self):
        self._manual_options()
        for w in self.saved_frame.winfo_children():
            w.destroy()
        outfits = self.repo.outfits()
        if not outfits:
            muted(self.saved_frame, "No saved outfits yet.").pack(pady=30)
            return
        for o in outfits:
            items = [it for it in (self.repo.get_item(i) for i in o.item_ids) if it]
            if not items:
                continue
            sub = f"{o.occasion} · saved {o.created.isoformat()}" + (f" · {o.notes}" if o.notes else "")
            OutfitStrip(self.saved_frame, items, o.name, sub,
                        actions=[("Delete", lambda o=o: self._delete(o)),
                                 ("Wear today", lambda o=o, items=items: self._wear(items, o.occasion, o.id))]).pack(fill="x", pady=6)

    def _delete(self, o: Outfit):
        if messagebox.askyesno("Delete outfit", f"Delete “{o.name}”?", parent=self):
            self.repo.delete_outfit(o.id)
            self.refresh()
            self.app.data_changed()
