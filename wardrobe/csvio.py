"""CSV export / import so you can bulk-edit the wardrobe in a spreadsheet."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from .db import Repository
from .images import placeholder_path
from .logic.colours import PALETTE, nearest_name
from .models import CATEGORIES, SEASONS, Item

COLUMNS = ["name", "category", "subtype", "colour", "colour_name", "pattern", "seasons", "formality",
           "warmth", "brand", "price", "purchased", "tags", "status", "favourite", "notes", "image_path"]


def export_items(repo: Repository, path: Path | str) -> int:
    items = repo.items()
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for it in items:
            w.writerow({
                "name": it.name, "category": it.category, "subtype": it.subtype, "colour": it.colour,
                "colour_name": it.colour_name, "pattern": it.pattern, "seasons": "|".join(it.seasons),
                "formality": it.formality, "warmth": it.warmth, "brand": it.brand, "price": it.price,
                "purchased": it.purchased.isoformat() if it.purchased else "", "tags": "|".join(it.tags),
                "status": it.status, "favourite": int(it.favourite), "notes": it.notes, "image_path": it.image_path,
            })
    return len(items)


def import_items(repo: Repository, path: Path | str) -> int:
    """Add rows as new items. Minimal required columns: name, category. Returns number added."""
    n = 0
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = (row.get("name") or "").strip()
            cat = (row.get("category") or "").strip().lower()
            if not name or cat not in CATEGORIES:
                continue
            colour = (row.get("colour") or "").strip()
            if colour and not colour.startswith("#"):
                colour = PALETTE.get(colour.lower(), "")
            cname = (row.get("colour_name") or "").strip().lower()
            if not colour and cname in PALETTE:
                colour = PALETTE[cname]
            colour = colour or "#808080"
            cname = cname or nearest_name(colour)
            seasons = [s for s in (row.get("seasons") or "").replace(",", "|").split("|") if s.strip() in SEASONS]
            it = Item(
                name=name, category=cat, subtype=(row.get("subtype") or "").strip(), colour=colour,
                colour_name=cname, pattern=(row.get("pattern") or "solid").strip() or "solid",
                seasons=seasons or list(SEASONS),
                formality=int(float(row.get("formality") or 3)), warmth=int(float(row.get("warmth") or 3)),
                brand=(row.get("brand") or "").strip(), price=float(row.get("price") or 0),
                purchased=date.fromisoformat(row["purchased"]) if row.get("purchased") else None,
                tags=[t.strip().lower() for t in (row.get("tags") or "").replace(",", "|").split("|") if t.strip()],
                status=(row.get("status") or "clean").strip() or "clean",
                favourite=str(row.get("favourite") or "0").strip().lower() in ("1", "true", "yes", "y"),
                notes=row.get("notes") or "", image_path=(row.get("image_path") or "").strip(),
            )
            if not it.image_path or not Path(it.image_path).exists():
                it.image_path = str(placeholder_path(it.subtype or "t-shirt", it.colour, it.pattern))
            repo.add_item(it)
            n += 1
    return n
