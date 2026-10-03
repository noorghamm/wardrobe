"""Plain dataclasses used across the app (no DB or UI code here)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

CATEGORIES = ["top", "bottom", "dress", "outerwear", "shoes", "bag", "accessory"]
SEASONS = ["spring", "summer", "autumn", "winter"]
PATTERNS = ["solid", "stripes", "dots", "check", "floral", "graphic", "lace", "velvet", "leopard"]
OCCASIONS = ["casual", "uni", "work", "date", "party", "formal", "gym", "travel"]
STATUSES = ["clean", "laundry"]

# formality: 1 = loungewear … 5 = black tie.  warmth: 1 = sheer/summer … 5 = heavy winter.
SUBTYPES = {
    "top": ["t-shirt", "baby tee", "shirt", "blouse", "corset top", "mesh top", "jumper", "hoodie",
            "cardigan", "tank", "turtleneck"],
    "bottom": ["jeans", "flared jeans", "cargo trousers", "trousers", "skirt", "maxi skirt", "shorts",
               "leggings", "joggers"],
    "dress": ["dress", "slip dress", "maxi dress", "jumpsuit", "abaya"],
    "outerwear": ["coat", "long coat", "jacket", "leather jacket", "blazer", "trench", "puffer", "denim jacket"],
    "shoes": ["sneakers", "boots", "platform boots", "mary janes", "heels", "loafers", "sandals", "flats"],
    "bag": ["tote", "crossbody", "shoulder bag", "backpack", "clutch"],
    "accessory": ["scarf", "hat", "belt", "choker", "jewellery", "sunglasses", "hijab", "tights"],
}


@dataclass
class Item:
    name: str
    category: str
    subtype: str = ""
    colour: str = "#808080"          # hex
    colour_name: str = "grey"
    pattern: str = "solid"
    seasons: list[str] = field(default_factory=lambda: list(SEASONS))
    formality: int = 3               # 1-5
    warmth: int = 3                  # 1-5
    brand: str = ""
    price: float = 0.0
    purchased: date | None = None
    image_path: str = ""             # relative to DATA_DIR, or absolute
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    status: str = "clean"
    favourite: bool = False
    id: int | None = None

    def fits_season(self, season: str) -> bool:
        return season in self.seasons


@dataclass
class Outfit:
    name: str
    item_ids: list[int]
    occasion: str = "casual"
    notes: str = ""
    score: float = 0.0
    created: date = field(default_factory=date.today)
    id: int | None = None


@dataclass
class WearLog:
    worn_on: date
    item_ids: list[int]
    outfit_id: int | None = None
    note: str = ""
    id: int | None = None


@dataclass
class PlanEntry:
    day: date
    outfit_id: int | None
    note: str = ""
    id: int | None = None
