"""Weekly planner: one saved outfit per day, auto-fill, mark worn."""
from __future__ import annotations

import random
from datetime import date, timedelta

import customtkinter as ctk

from ..logic.outfits import generate, outfit_name
from ..models import Outfit
from .widgets import ACCENT, CARD, Toast, accent_button, ghost_button, h1, h2, item_image, muted

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class PlannerView(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.repo = app.repo
        today = date.today()
        self.monday = today - timedelta(days=today.weekday())
        self._build()
        self.refresh()

    def _build(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(18, 6))
        h1(head, "Planner").pack(side="left")
        ghost_button(head, "‹", command=lambda: self._shift(-7), width=36).pack(side="left", padx=(16, 2))
        self.week_lbl = muted(head, "")
        self.week_lbl.pack(side="left", padx=6, pady=(6, 0))
        ghost_button(head, "›", command=lambda: self._shift(7), width=36).pack(side="left", padx=2)
        ghost_button(head, "Today", command=self._today, width=70).pack(side="left", padx=8)
        accent_button(head, "Auto-fill empty days", command=self.autofill, width=170).pack(side="right")
        muted(head, "uni on weekdays, casual at weekends, 14°C").pack(side="right", padx=10, pady=(6, 0))
        self.grid_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True, padx=12)
        self.toast = Toast(self)

    def _shift(self, days: int):
        self.monday += timedelta(days=days)
        self.refresh()

    def _today(self):
        t = date.today()
        self.monday = t - timedelta(days=t.weekday())
        self.refresh()

    def refresh(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        end = self.monday + timedelta(days=6)
        self.week_lbl.configure(text=f"{self.monday.strftime('%d %b')} – {end.strftime('%d %b %Y')}")
        plan = self.repo.plan_for_week(self.monday)
        outfits = self.repo.outfits()
        names = ["— none —"] + [o.name for o in outfits]
        by_name = {o.name: o for o in outfits}
        today = date.today()
        for k, (d, entry) in enumerate(plan.items()):
            card = ctk.CTkFrame(self.grid_frame, fg_color=CARD, corner_radius=14,
                                border_width=2 if d == today else 0, border_color=ACCENT)
            card.pack(fill="x", pady=5)
            left = ctk.CTkFrame(card, fg_color="transparent", width=230)
            left.pack(side="left", padx=12, pady=10)
            left.pack_propagate(False)
            h2(left, f"{DAYS[k]}  ·  {d.strftime('%d %b')}").pack(anchor="w")
            menu = ctk.CTkOptionMenu(left, values=names, width=206, dynamic_resizing=False,
                                     fg_color=ACCENT, button_color=ACCENT,
                                     command=lambda v, d=d: self._set(d, by_name.get(v)))
            cur = self.repo.get_outfit(entry.outfit_id) if entry.outfit_id else None
            menu.set(cur.name if cur else "— none —")
            menu.pack(anchor="w", pady=(6, 0))
            ctk.CTkFrame(left, fg_color="transparent", height=0).pack()
            strip = ctk.CTkFrame(card, fg_color="transparent")
            strip.pack(side="left", fill="x", expand=True, padx=6)
            if cur:
                for iid in cur.item_ids:
                    it = self.repo.get_item(iid)
                    if it:
                        ctk.CTkLabel(strip, text="", image=item_image(it, 72)).pack(side="left", padx=3, pady=8)
                right = ctk.CTkFrame(card, fg_color="transparent")
                right.pack(side="right", padx=12)
                ghost_button(right, "Wore it", width=90,
                             command=lambda o=cur, d=d: self._wore(o, d)).pack(pady=2)
            else:
                muted(strip, "nothing planned").pack(side="left", padx=8)

    def _set(self, d: date, outfit: Outfit | None):
        self.repo.set_plan(d, outfit.id if outfit else None)
        self.refresh()

    def _wore(self, o: Outfit, d: date):
        self.repo.log_wear(o.item_ids, outfit_id=o.id, worn_on=d)
        self.toast.show(f"Logged “{o.name}” for {d.strftime('%a %d %b')}")
        self.app.data_changed()

    def autofill(self):
        items = self.repo.items()
        plan = self.repo.plan_for_week(self.monday)
        rng = random.Random()
        made = 0
        used: set[int] = set()
        for d, entry in plan.items():
            if entry.outfit_id:
                continue
            occ = "uni" if d.weekday() < 5 else "casual"
            sugs = generate(items, occ, 14, False, wear_counts=self.repo.wear_counts(), n=6, rng=rng)
            pick = next((s for s in sugs if not (set(s.item_ids) & used)), sugs[0] if sugs else None)
            if not pick:
                continue
            used |= set(i.id for i in pick.items if i.category in ("top", "bottom", "dress"))
            o = self.repo.add_outfit(Outfit(name=f"{d.strftime('%a %d %b')} · {outfit_name(pick.items, occ)}",
                                            item_ids=pick.item_ids, occasion=occ, score=pick.score))
            self.repo.set_plan(d, o.id)
            made += 1
        self.toast.show(f"Planned {made} day(s)" if made else "Week already planned")
        self.refresh()
        self.app.data_changed()
