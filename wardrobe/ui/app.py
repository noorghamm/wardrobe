"""Main window: sidebar navigation + swappable views."""
from __future__ import annotations

import customtkinter as ctk

from .. import DB_PATH, __version__
from ..db import Repository
from .outfit_view import OutfitView
from .planner_view import PlannerView
from .stats_view import StatsView
from .wardrobe_view import WardrobeView
from .widgets import ACCENT, FONT, MUTED

SIDEBAR = ("#efe9e1", "#1d1b19")


class App(ctk.CTk):
    def __init__(self, db_path=DB_PATH):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title("Wardrobe")
        self.geometry("1200x780")
        self.minsize(980, 640)
        self.configure(fg_color=("#faf7f2", "#141414"))
        self.repo = Repository(db_path)

        self.sidebar = ctk.CTkFrame(self, width=190, corner_radius=0, fg_color=SIDEBAR)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        ctk.CTkLabel(self.sidebar, text="Wardrobe", font=ctk.CTkFont(FONT, 22, "bold")).pack(pady=(26, 2), padx=20, anchor="w")
        ctk.CTkLabel(self.sidebar, text="what to wear, sorted", text_color=MUTED, font=ctk.CTkFont(FONT, 12)).pack(padx=20, anchor="w", pady=(0, 20))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True)

        self.views: dict[str, ctk.CTkFrame] = {}
        self.nav: dict[str, ctk.CTkButton] = {}
        for name, cls in (("Wardrobe", WardrobeView), ("Outfits", OutfitView),
                          ("Planner", PlannerView), ("Stats", StatsView)):
            b = ctk.CTkButton(self.sidebar, text=name, anchor="w", height=40, corner_radius=10,
                              fg_color="transparent", text_color=("#222222", "#eeeeee"),
                              hover_color=("#e3dbd0", "#2a2725"), font=ctk.CTkFont(FONT, 14),
                              command=lambda n=name: self.show(n))
            b.pack(fill="x", padx=12, pady=3)
            self.nav[name] = b
            self._view_classes = getattr(self, "_view_classes", {})
            self._view_classes[name] = cls

        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=12, pady=16)
        self.theme = ctk.CTkSwitch(bottom, text="Dark mode", command=self._toggle_theme,
                                   progress_color=ACCENT, button_color=ACCENT)
        self.theme.pack(anchor="w", pady=(0, 8))
        ctk.CTkLabel(bottom, text=f"v{__version__} · data in\n{DB_PATH.parent.name}/", text_color=MUTED,
                     font=ctk.CTkFont(FONT, 11), justify="left").pack(anchor="w")

        self.current: str | None = None
        self.show("Wardrobe")
        self.protocol("WM_DELETE_WINDOW", self._close)

    def show(self, name: str):
        if self.current == name:
            self.views[name].refresh()
            return
        if self.current:
            self.views[self.current].pack_forget()
            self.nav[self.current].configure(fg_color="transparent")
        if name not in self.views:
            self.views[name] = self._view_classes[name](self.content, self)
        else:
            self.views[name].refresh()
        self.views[name].pack(fill="both", expand=True)
        self.nav[name].configure(fg_color=("#e3dbd0", "#2a2725"))
        self.current = name

    def data_changed(self):
        """Something was edited in one view. Views refresh themselves in show(), so nothing to do yet;
        kept as a single hook in case a view ever needs an eager refresh."""

    def _toggle_theme(self):
        ctk.set_appearance_mode("dark" if self.theme.get() else "light")

    def _close(self):
        self.repo.close()
        self.destroy()
