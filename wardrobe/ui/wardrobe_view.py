"""The catalogue: filter bar + grid of item cards."""
from __future__ import annotations

from tkinter import filedialog, messagebox

import customtkinter as ctk

from ..csvio import export_items, import_items
from ..models import CATEGORIES, SEASONS, Item
from .item_dialog import ItemDialog
from .widgets import ACCENT, ItemCard, Toast, accent_button, ghost_button, h1, muted

COLS = 5


class WardrobeView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.repo = app.repo
        self._build()
        self.refresh()

    def _build(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(18, 6))
        h1(head, "Wardrobe").pack(side="left")
        self.count_lbl = muted(head, "")
        self.count_lbl.pack(side="left", padx=12, pady=(6, 0))
        accent_button(head, "+ Add item", command=self.add_item, width=110).pack(side="right")
        ghost_button(head, "Load demo wardrobe", command=self._seed, width=160).pack(side="right", padx=8)
        ghost_button(head, "Import CSV", command=self._import_csv, width=100).pack(side="right", padx=(0, 4))
        ghost_button(head, "Export CSV", command=self._export_csv, width=100).pack(side="right", padx=(0, 4))

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=20, pady=(0, 8))
        self.search = ctk.CTkEntry(bar, placeholder_text="Search name, brand, colour, tag…", width=260)
        self.search.pack(side="left")
        self.search.bind("<KeyRelease>", lambda e: self.refresh())
        self.cat = ctk.CTkSegmentedButton(bar, values=["all"] + CATEGORIES, command=lambda _: self.refresh(),
                                          selected_color=ACCENT, selected_hover_color=ACCENT)
        self.cat.set("all")
        self.cat.pack(side="left", padx=12)
        self.season = ctk.CTkOptionMenu(bar, values=["all"] + SEASONS, width=110, command=lambda _: self.refresh(),
                                        fg_color=ACCENT, button_color=ACCENT)
        self.season.set("all")
        self.season.pack(side="left")
        self.status = ctk.CTkOptionMenu(bar, values=["all", "clean", "laundry"], width=100,
                                        command=lambda _: self.refresh(), fg_color=ACCENT, button_color=ACCENT)
        self.status.set("all")
        self.status.pack(side="left", padx=8)
        self.fav_only = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(bar, text="★ only", variable=self.fav_only, command=self.refresh,
                        fg_color=ACCENT, hover_color=ACCENT, width=80).pack(side="left")

        self.grid_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=12)
        for c in range(COLS):
            self.grid_frame.grid_columnconfigure(c, weight=1)
        self.toast = Toast(self)

    # ---------- data ----------
    def refresh(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        items = self.repo.items(category=self.cat.get(), season=self.season.get(),
                                search=self.search.get(), status=self.status.get(),
                                favourites_only=self.fav_only.get())
        wears = self.repo.wear_counts()
        self.count_lbl.configure(text=f"{len(items)} of {self.repo.count_items()} items")
        if not items:
            msg = "Your wardrobe is empty — add an item or load the demo wardrobe." if not self.repo.count_items() \
                else "Nothing matches those filters."
            muted(self.grid_frame, msg).grid(row=0, column=0, columnspan=COLS, pady=40)
            return
        for k, it in enumerate(items):
            card = ItemCard(self.grid_frame, it, on_click=self.edit_item, wears=wears.get(it.id, 0))
            card.grid(row=k // COLS, column=k % COLS, padx=8, pady=8, sticky="n")

    def add_item(self):
        ItemDialog(self, None, on_save=self._saved)

    def edit_item(self, item: Item):
        ItemDialog(self, item, on_save=self._saved, on_delete=self._deleted)

    def _saved(self, item: Item):
        if item.id:
            self.repo.update_item(item)
            self.toast.show(f"Saved {item.name}")
        else:
            self.repo.add_item(item)
            self.toast.show(f"Added {item.name}")
        self.refresh()
        self.app.data_changed()

    def _deleted(self, item: Item):
        self.repo.delete_item(item.id)
        self.toast.show(f"Deleted {item.name}")
        self.refresh()
        self.app.data_changed()

    def _seed(self):
        from ..seed import seed
        n = seed(self.repo)
        self.toast.show(f"Added {n} demo items" if n else "Wardrobe already has items — demo not loaded")
        self.refresh()
        self.app.data_changed()

    def _export_csv(self):
        p = filedialog.asksaveasfilename(title="Export wardrobe", defaultextension=".csv",
                                         initialfile="wardrobe.csv", filetypes=[("CSV", "*.csv")])
        if p:
            n = export_items(self.repo, p)
            self.toast.show(f"Exported {n} items to {p}")

    def _import_csv(self):
        p = filedialog.askopenfilename(title="Import wardrobe CSV", filetypes=[("CSV", "*.csv")])
        if not p:
            return
        try:
            n = import_items(self.repo, p)
        except Exception as e:  # bad CSV
            messagebox.showerror("Import failed", str(e), parent=self)
            return
        self.toast.show(f"Imported {n} items")
        self.refresh()
        self.app.data_changed()
