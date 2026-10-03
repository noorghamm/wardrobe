"""Seed a demo wardrobe (~45 pieces) with generated placeholder images and a bit of wear history."""
from __future__ import annotations

import random
from datetime import date, timedelta

from .db import Repository
from .images import placeholder_path
from .logic.colours import PALETTE
from .models import Item, Outfit

ALL = ["spring", "summer", "autumn", "winter"]
WARM = ["spring", "summer"]
COLD = ["autumn", "winter"]
MID = ["spring", "autumn", "winter"]

# name, category, subtype, colour name, pattern, seasons, formality, warmth, brand, price, tags
SEED = [
    # tops
    ("White tee", "top", "t-shirt", "white", "solid", ALL, 1, 1, "Uniqlo", 9.9, ["basic"]),
    ("Black tee", "top", "t-shirt", "black", "solid", ALL, 1, 1, "Uniqlo", 9.9, ["basic"]),
    ("Striped breton top", "top", "t-shirt", "navy", "stripes", ALL, 2, 2, "Petit Bateau", 45, []),
    ("Sage linen shirt", "top", "shirt", "sage", "solid", WARM, 2, 1, "COS", 69, []),
    ("White poplin shirt", "top", "shirt", "white", "solid", ALL, 4, 2, "Arket", 59, ["work"]),
    ("Sky blue oxford shirt", "top", "shirt", "sky blue", "solid", ALL, 3, 2, "Ralph Lauren", 89, ["work"]),
    ("Cream silk blouse", "top", "blouse", "cream", "solid", MID, 4, 2, "& Other Stories", 75, ["work", "date"]),
    ("Burgundy knit", "top", "jumper", "burgundy", "solid", COLD, 3, 4, "COS", 85, []),
    ("Grey merino jumper", "top", "jumper", "grey", "solid", COLD, 3, 4, "Uniqlo", 39.9, ["basic"]),
    ("Black turtleneck", "top", "turtleneck", "black", "solid", COLD, 3, 3, "Uniqlo", 29.9, ["basic"]),
    ("Lilac hoodie", "top", "hoodie", "lilac", "graphic", MID, 1, 4, "Nike", 55, ["gym", "lounge"]),
    ("Camel cardigan", "top", "cardigan", "camel", "solid", MID, 2, 3, "Massimo Dutti", 79, []),
    ("Mustard check shirt", "top", "shirt", "mustard", "check", MID, 2, 3, "Levi's", 60, []),
    ("Black gym tank", "top", "tank", "black", "solid", ALL, 1, 1, "Gymshark", 24, ["gym", "sport"]),
    # bottoms
    ("Mid-wash straight jeans", "bottom", "jeans", "denim", "solid", ALL, 2, 3, "Levi's", 95, ["basic"]),
    ("Black wide-leg jeans", "bottom", "jeans", "black", "solid", ALL, 2, 3, "Weekday", 60, []),
    ("Charcoal tailored trousers", "bottom", "trousers", "charcoal", "solid", ALL, 4, 3, "COS", 89, ["work"]),
    ("Cream pleated trousers", "bottom", "trousers", "cream", "solid", WARM, 3, 2, "Zara", 49.9, []),
    ("Black satin midi skirt", "bottom", "skirt", "black", "solid", ALL, 4, 2, "& Other Stories", 65, ["date", "party"]),
    ("Denim mini skirt", "bottom", "skirt", "denim", "solid", WARM, 1, 1, "Levi's", 55, []),
    ("Beige linen shorts", "bottom", "shorts", "beige", "solid", ["summer"], 1, 1, "Arket", 45, []),
    ("Black leggings", "bottom", "leggings", "black", "solid", ALL, 1, 2, "Gymshark", 40, ["gym", "sport", "lounge"]),
    ("Grey joggers", "bottom", "joggers", "grey", "solid", MID, 1, 3, "Nike", 50, ["gym", "sport", "lounge"]),
    # dresses
    ("Sage floral midi dress", "dress", "dress", "sage", "floral", WARM, 3, 1, "Rixo", 185, ["date"]),
    ("Black slip dress", "dress", "dress", "black", "solid", ALL, 4, 1, "Reformation", 150, ["party", "date"]),
    ("Navy shirt dress", "dress", "dress", "navy", "solid", MID, 3, 2, "COS", 99, ["work"]),
    ("Plum velvet dress", "dress", "dress", "plum", "solid", COLD, 5, 3, "Ghost", 160, ["formal", "party"]),
    # outerwear
    ("Camel wool coat", "outerwear", "coat", "camel", "solid", COLD, 4, 5, "Massimo Dutti", 229, []),
    ("Black puffer", "outerwear", "puffer", "black", "solid", ["winter"], 1, 5, "The North Face", 250, []),
    ("Navy blazer", "outerwear", "blazer", "navy", "solid", ALL, 4, 3, "Zara", 89.9, ["work"]),
    ("Denim jacket", "outerwear", "denim jacket", "denim", "solid", MID, 2, 3, "Levi's", 110, []),
    ("Beige trench", "outerwear", "trench", "beige", "solid", MID, 3, 3, "Mango", 120, []),
    ("Olive bomber", "outerwear", "jacket", "olive", "solid", MID, 2, 3, "Alpha Industries", 140, []),
    # shoes
    ("White leather sneakers", "shoes", "sneakers", "white", "solid", ALL, 2, 2, "Veja", 120, ["basic"]),
    ("Black chelsea boots", "shoes", "boots", "black", "solid", COLD, 3, 4, "Dr. Martens", 169, []),
    ("Chocolate knee boots", "shoes", "boots", "chocolate", "solid", COLD, 4, 4, "Vagabond", 180, []),
    ("Black loafers", "shoes", "loafers", "black", "solid", ALL, 4, 2, "Bass Weejuns", 150, ["work"]),
    ("Red heels", "shoes", "heels", "red", "solid", ALL, 5, 1, "Mango", 59.9, ["party", "formal"]),
    ("Tan sandals", "shoes", "sandals", "camel", "solid", ["summer"], 2, 1, "Birkenstock", 85, []),
    ("Running trainers", "shoes", "sneakers", "coral", "solid", ALL, 1, 2, "Nike", 110, ["gym", "sport"]),
    # bags
    ("Beige canvas tote", "bag", "tote", "beige", "solid", ALL, 2, 1, "Arket", 25, ["uni"]),
    ("Black leather crossbody", "bag", "crossbody", "black", "solid", ALL, 4, 1, "Polène", 320, []),
    ("Navy backpack", "bag", "backpack", "navy", "solid", ALL, 1, 1, "Fjällräven", 85, ["uni"]),
    ("Silver clutch", "bag", "clutch", "silver", "solid", ALL, 5, 1, "Zara", 35.9, ["party", "formal"]),
    # accessories
    ("Mustard wool scarf", "accessory", "scarf", "mustard", "solid", COLD, 2, 4, "Acne Studios", 150, []),
    ("Black beanie", "accessory", "hat", "black", "solid", COLD, 1, 4, "Carhartt", 25, []),
    ("Cream silk hijab", "accessory", "hijab", "cream", "solid", ALL, 3, 1, "", 20, []),
    ("Tortoise sunglasses", "accessory", "sunglasses", "brown", "solid", WARM, 2, 1, "Ray-Ban", 160, []),
]


def seed(repo: Repository, with_history: bool = True, rng: random.Random | None = None) -> int:
    """Insert the demo wardrobe. Returns number of items added. No-op if the wardrobe isn't empty."""
    if repo.count_items():
        return 0
    rng = rng or random.Random(7)
    today = date.today()
    items: list[Item] = []
    for name, cat, sub, cname, pat, seasons, form, warm, brand, price, tags in SEED:
        colour = PALETTE[cname]
        img = placeholder_path(sub, colour, pat)
        it = Item(name=name, category=cat, subtype=sub, colour=colour, colour_name=cname, pattern=pat,
                  seasons=list(seasons), formality=form, warmth=warm, brand=brand, price=price,
                  purchased=today - timedelta(days=rng.randint(30, 900)),
                  image_path=str(img), tags=list(tags),
                  favourite=name in ("Camel wool coat", "White leather sneakers", "Black slip dress"))
        items.append(repo.add_item(it))

    if with_history:
        by_name = {i.name: i for i in items}

        def o(name, occasion, *names):
            return repo.add_outfit(Outfit(name=name, item_ids=[by_name[n].id for n in names],
                                          occasion=occasion, score=0.0))

        outfits = [
            o("Uni default", "uni", "Striped breton top", "Mid-wash straight jeans", "White leather sneakers",
              "Beige canvas tote"),
            o("Office Monday", "work", "White poplin shirt", "Charcoal tailored trousers", "Black loafers",
              "Navy blazer", "Black leather crossbody"),
            o("Cold snap", "casual", "Grey merino jumper", "Black wide-leg jeans", "Black chelsea boots",
              "Camel wool coat", "Mustard wool scarf"),
            o("Dinner", "date", "Black slip dress", "Red heels", "Black leather crossbody"),
            o("Gym", "gym", "Black gym tank", "Black leggings", "Running trainers"),
        ]
        # spread ~40 wears over the last 90 days
        for k in range(40):
            d = today - timedelta(days=rng.randint(0, 90))
            of = rng.choice(outfits)
            repo.log_wear(of.item_ids, outfit_id=of.id, worn_on=d)
        # plan the current week lightly
        monday = today - timedelta(days=today.weekday())
        repo.set_plan(monday, outfits[0].id)
        repo.set_plan(monday + timedelta(days=1), outfits[1].id)
        repo.set_plan(monday + timedelta(days=4), outfits[3].id)
    return len(items)
