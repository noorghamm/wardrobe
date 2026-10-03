"""Stats: headline numbers, most/never worn, cost per wear, colour and category breakdowns."""
from __future__ import annotations

import customtkinter as ctk

from ..logic import stats
from ..logic.colours import PALETTE
from .widgets import ACCENT, CARD, MUTED, h1, h2, item_image, muted


class StatsView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.repo = app.repo
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(18, 6))
        h1(head, "Stats").pack(side="left")
        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=12)
        self.refresh()

    def _tile(self, master, value: str, label: str):
        t = ctk.CTkFrame(master, fg_color=CARD, corner_radius=14)
        ctk.CTkLabel(t, text=value, font=ctk.CTkFont("Helvetica", 26, "bold")).pack(padx=18, pady=(12, 0))
        muted(t, label, anchor="center").pack(padx=18, pady=(0, 12))
        return t

    def _section(self, title: str):
        f = ctk.CTkFrame(self.body, fg_color=CARD, corner_radius=14)
        f.pack(fill="x", pady=6)
        h2(f, title).pack(anchor="w", padx=14, pady=(10, 4))
        return f

    def _item_row(self, master, st: stats.ItemStat, right: str):
        r = ctk.CTkFrame(master, fg_color="transparent")
        r.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(r, text="", image=item_image(st.item, 44)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(r, text=st.item.name, anchor="w").pack(side="left")
        muted(r, right).pack(side="right", padx=8)

    def _bar(self, master, label: str, n: int, total: int, colour: str | None = None):
        r = ctk.CTkFrame(master, fg_color="transparent")
        r.pack(fill="x", padx=14, pady=2)
        muted(r, label, width=110).pack(side="left")
        bar = ctk.CTkProgressBar(r, progress_color=colour or ACCENT, height=10)
        bar.set(n / total if total else 0)
        bar.pack(side="left", fill="x", expand=True, padx=8)
        muted(r, str(n), width=30).pack(side="left")

    def refresh(self):
        for w in self.body.winfo_children():
            w.destroy()
        items = self.repo.items()
        logs = self.repo.wear_log()
        st = stats.item_stats(items, logs)
        outfits = self.repo.outfits()

        tiles = ctk.CTkFrame(self.body, fg_color="transparent")
        tiles.pack(fill="x", pady=(4, 8))
        for k, (v, l) in enumerate([
            (str(len(items)), "items"), (str(len(outfits)), "saved outfits"),
            (str(stats.wears_in_period(logs, 30)), "wears · last 30 days"),
            (f"£{stats.wardrobe_value(items):,.0f}", "wardrobe value"),
            (f"{len(stats.never_worn(st))}", "never worn"),
        ]):
            self._tile(tiles, v, l).pack(side="left", padx=4, fill="x", expand=True)

        if not items:
            muted(self.body, "Add some items first.").pack(pady=30)
            return

        two = ctk.CTkFrame(self.body, fg_color="transparent")
        two.pack(fill="x")
        two.grid_columnconfigure((0, 1), weight=1, uniform="c")

        left = ctk.CTkFrame(two, fg_color=CARD, corner_radius=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 4), pady=6)
        h2(left, "Most worn").pack(anchor="w", padx=14, pady=(10, 4))
        mw = stats.most_worn(st, 6)
        if not mw:
            muted(left, "Nothing logged yet — use “Wear today” on an outfit.").pack(anchor="w", padx=14, pady=(0, 10))
        for s in mw:
            self._item_row(left, s, f"{s.wears}× · last {s.last_worn.strftime('%d %b')}")
        ctk.CTkLabel(left, text="").pack()

        right = ctk.CTkFrame(two, fg_color=CARD, corner_radius=14)
        right.grid(row=0, column=1, sticky="nsew", padx=(4, 0), pady=6)
        h2(right, "Best value (cost per wear)").pack(anchor="w", padx=14, pady=(10, 4))
        bv = stats.best_value(st, 6)
        if not bv:
            muted(right, "Add prices and log wears to see this.").pack(anchor="w", padx=14, pady=(0, 10))
        for s in bv:
            self._item_row(right, s, f"£{s.cost_per_wear:.2f}/wear · £{s.item.price:.0f}")
        ctk.CTkLabel(right, text="").pack()

        nw = stats.never_worn(st)
        f = self._section(f"Never worn ({len(nw)}) — wear it or let it go")
        grid = ctk.CTkFrame(f, fg_color="transparent")
        grid.pack(fill="x", padx=10, pady=(0, 10))
        for k, s in enumerate(nw[:20]):
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=k // 10, column=k % 10, padx=4, pady=4)
            ctk.CTkLabel(cell, text="", image=item_image(s.item, 64)).pack()
            muted(cell, s.item.name[:13], anchor="center").pack()
        if len(nw) > 20:
            muted(f, f"…and {len(nw) - 20} more").pack(anchor="w", padx=14, pady=(0, 8))
        if not nw:
            muted(f, "Everything has been worn at least once.").pack(anchor="w", padx=14, pady=(0, 10))

        stale = stats.not_worn_since(st, 90)
        if stale:
            f = self._section(f"Not worn in 90+ days ({len(stale)})")
            for s in stale[:8]:
                self._item_row(f, s, f"last {s.last_worn.strftime('%d %b %Y')}")
            ctk.CTkLabel(f, text="").pack()

        f = self._section("Colours")
        cb = stats.colour_breakdown(items)
        for name, n in cb[:10]:
            self._bar(f, name, n, len(items), PALETTE.get(name))
        ctk.CTkLabel(f, text="").pack()

        f = self._section("Categories")
        for name, n in stats.category_breakdown(items):
            self._bar(f, name, n, len(items))
        ctk.CTkLabel(f, text="").pack()
