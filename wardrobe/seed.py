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
    # ---- tops: baby tees, corsets, lace, knits ----
    ("Black baby tee", "top", "baby tee", "black", "solid", ALL, 1, 1, "Brandy Melville", 18, ["basic", "2000s"]),
    ("Cream baby tee", "top", "baby tee", "cream", "solid", ALL, 1, 1, "Brandy Melville", 18, ["basic", "2000s"]),
    ("Oxblood graphic baby tee", "top", "baby tee", "oxblood", "graphic", ALL, 1, 1, "Depop find", 12, ["2000s"]),
    ("Black lace long-sleeve", "top", "mesh top", "black", "lace", MID, 3, 2, "Urban Outfitters", 32, ["witchy", "layer"]),
    ("Black mesh top", "top", "mesh top", "black", "solid", ALL, 2, 1, "Depop find", 10, ["layer", "2000s"]),
    ("Plum velvet corset top", "top", "corset top", "plum", "velvet", MID, 4, 2, "Free People", 68, ["witchy", "date", "party"]),
    ("Chocolate satin corset", "top", "corset top", "chocolate", "solid", ALL, 4, 1, "Zara", 35.9, ["party", "date"]),
    ("Forest ribbed cardigan", "top", "cardigan", "forest", "solid", MID, 2, 3, "Vintage", 22, ["autumn"]),
    ("Mustard chunky cardigan", "top", "cardigan", "ochre", "solid", COLD, 2, 4, "& Other Stories", 85, ["autumn"]),
    ("Burgundy turtleneck", "top", "turtleneck", "burgundy", "solid", COLD, 3, 3, "Uniqlo", 29.9, ["basic", "autumn"]),
    ("Black turtleneck", "top", "turtleneck", "black", "solid", COLD, 3, 3, "Uniqlo", 29.9, ["basic"]),
    ("Moss mohair jumper", "top", "jumper", "moss", "solid", COLD, 2, 5, "Vintage", 40, ["autumn", "witchy"]),
    ("Charcoal fitted knit", "top", "jumper", "charcoal", "solid", COLD, 3, 4, "COS", 79, ["basic"]),
    ("Ink pinstripe shirt", "top", "shirt", "ink", "stripes", MID, 4, 2, "Vintage", 25, ["work", "dark academia"]),
    ("Cream lace blouse", "top", "blouse", "cream", "lace", MID, 3, 2, "Vintage", 28, ["witchy"]),
    ("Rust band tee", "top", "t-shirt", "rust", "graphic", ALL, 1, 1, "Gig merch", 25, ["2000s"]),
    ("Black zip hoodie", "top", "hoodie", "black", "solid", MID, 1, 4, "Carhartt", 90, ["lounge", "2000s"]),
    ("Black gym tank", "top", "tank", "black", "solid", ALL, 1, 1, "Gymshark", 24, ["gym", "sport"]),
    # ---- bottoms: flares, cargos, minis, maxis ----
    ("Black low-rise flares", "bottom", "flared jeans", "black", "solid", ALL, 2, 3, "Weekday", 60, ["2000s"]),
    ("Dark indigo flares", "bottom", "flared jeans", "ink", "solid", ALL, 2, 3, "Levi's", 110, ["2000s", "basic"]),
    ("Chocolate cargo trousers", "bottom", "cargo trousers", "chocolate", "solid", MID, 1, 3, "Dickies", 70, ["2000s"]),
    ("Black cargo trousers", "bottom", "cargo trousers", "black", "solid", ALL, 1, 3, "Dickies", 70, ["2000s"]),
    ("Charcoal pleated trousers", "bottom", "trousers", "charcoal", "solid", ALL, 4, 3, "COS", 89, ["work", "dark academia"]),
    ("Plaid pleated mini skirt", "bottom", "skirt", "burgundy", "check", MID, 2, 2, "Vintage", 20, ["2000s", "dark academia"]),
    ("Black mini skirt", "bottom", "skirt", "black", "solid", ALL, 2, 1, "Zara", 25.9, ["2000s"]),
    ("Black tiered maxi skirt", "bottom", "maxi skirt", "black", "solid", ALL, 2, 2, "Free People", 78, ["witchy"]),
    ("Aubergine velvet maxi skirt", "bottom", "maxi skirt", "aubergine", "velvet", COLD, 3, 3, "Vintage", 30, ["witchy"]),
    ("Black leggings", "bottom", "leggings", "black", "solid", ALL, 1, 2, "Gymshark", 40, ["gym", "sport", "lounge"]),
    ("Grey joggers", "bottom", "joggers", "grey", "solid", MID, 1, 3, "Nike", 50, ["gym", "sport", "lounge"]),
    # ---- dresses ----
    ("Black slip dress", "dress", "slip dress", "black", "solid", ALL, 3, 1, "Reformation", 150, ["witchy", "layer", "date"]),
    ("Oxblood satin slip dress", "dress", "slip dress", "oxblood", "solid", ALL, 4, 1, "& Other Stories", 85, ["party", "date"]),
    ("Black lace maxi dress", "dress", "maxi dress", "black", "lace", MID, 4, 2, "Vintage", 45, ["witchy", "formal"]),
    ("Forest velvet midi dress", "dress", "dress", "forest", "velvet", COLD, 5, 3, "Ghost", 160, ["formal", "party", "witchy"]),
    ("Dusty rose babydoll dress", "dress", "dress", "dusty rose", "floral", WARM, 2, 1, "Depop find", 22, ["2000s"]),
    # ---- outerwear ----
    ("Black wool long coat", "outerwear", "long coat", "black", "solid", COLD, 4, 5, "Vintage", 95, ["witchy", "dark academia"]),
    ("Oxblood leather jacket", "outerwear", "leather jacket", "oxblood", "solid", MID, 3, 3, "Vintage", 120, ["2000s", "witchy"]),
    ("Black leather jacket", "outerwear", "leather jacket", "black", "solid", MID, 3, 3, "AllSaints", 350, ["basic"]),
    ("Camel trench", "outerwear", "trench", "camel", "solid", MID, 3, 3, "Mango", 120, ["dark academia"]),
    ("Chocolate corduroy blazer", "outerwear", "blazer", "chocolate", "solid", MID, 4, 3, "Vintage", 35, ["dark academia", "work"]),
    ("Black puffer", "outerwear", "puffer", "black", "solid", ["winter"], 1, 5, "The North Face", 250, []),
    ("Leopard faux-fur coat", "outerwear", "coat", "camel", "leopard", COLD, 3, 5, "Vintage", 60, ["2000s", "party"]),
    # ---- shoes ----
    ("Black platform boots", "shoes", "platform boots", "black", "solid", MID, 2, 4, "Dr. Martens", 189, ["witchy", "2000s"]),
    ("Chocolate knee boots", "shoes", "boots", "chocolate", "solid", COLD, 4, 4, "Vagabond", 180, ["autumn"]),
    ("Black mary janes", "shoes", "mary janes", "black", "solid", ALL, 3, 2, "Vagabond", 110, ["witchy", "dark academia"]),
    ("Oxblood loafers", "shoes", "loafers", "oxblood", "solid", ALL, 4, 2, "Bass Weejuns", 150, ["work", "dark academia"]),
    ("Black heels", "shoes", "heels", "black", "solid", ALL, 5, 1, "Mango", 59.9, ["party", "formal"]),
    ("Beat-up white sneakers", "shoes", "sneakers", "white", "solid", ALL, 1, 2, "Converse", 65, ["basic", "2000s"]),
    ("Running trainers", "shoes", "sneakers", "coral", "solid", ALL, 1, 2, "Nike", 110, ["gym", "sport"]),
    # ---- bags ----
    ("Black baguette shoulder bag", "bag", "shoulder bag", "black", "solid", ALL, 3, 1, "Vintage", 40, ["2000s"]),
    ("Oxblood leather shoulder bag", "bag", "shoulder bag", "oxblood", "solid", ALL, 4, 1, "Polène", 320, []),
    ("Black canvas tote", "bag", "tote", "black", "solid", ALL, 2, 1, "Arket", 25, ["uni"]),
    ("Chocolate leather satchel", "bag", "crossbody", "chocolate", "solid", ALL, 3, 1, "Vintage", 55, ["uni", "dark academia"]),
    ("Silver mesh clutch", "bag", "clutch", "silver", "solid", ALL, 5, 1, "Vintage", 30, ["party", "2000s"]),
    # ---- accessories ----
    ("Black velvet choker", "accessory", "choker", "black", "velvet", ALL, 2, 1, "Etsy", 12, ["witchy", "2000s"]),
    ("Chunky silver belt", "accessory", "belt", "silver", "solid", ALL, 2, 1, "Vintage", 25, ["2000s"]),
    ("Chocolate leather belt", "accessory", "belt", "chocolate", "solid", ALL, 3, 1, "Vintage", 18, []),
    ("Black sheer tights", "accessory", "tights", "black", "solid", MID, 3, 2, "Calzedonia", 10, ["witchy"]),
    ("Burgundy wool scarf", "accessory", "scarf", "burgundy", "solid", COLD, 2, 4, "Acne Studios", 150, ["autumn"]),
    ("Black beanie", "accessory", "hat", "black", "solid", COLD, 1, 4, "Carhartt", 25, []),
    ("Cream silk hijab", "accessory", "hijab", "cream", "solid", ALL, 3, 1, "", 20, []),
    ("Black chiffon hijab", "accessory", "hijab", "black", "solid", ALL, 3, 1, "", 20, []),
    ("Silver moon pendant", "accessory", "jewellery", "silver", "solid", ALL, 2, 1, "Etsy", 28, ["witchy"]),
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
                  favourite=name in ("Black wool long coat", "Black platform boots", "Black slip dress", "Plum velvet corset top"))
        items.append(repo.add_item(it))

    if with_history:
        by_name = {i.name: i for i in items}

        def o(name, occasion, *names):
            return repo.add_outfit(Outfit(name=name, item_ids=[by_name[n].id for n in names],
                                          occasion=occasion, score=0.0))

        outfits = [
            o("Uni default", "uni", "Black baby tee", "Dark indigo flares", "Black platform boots",
              "Oxblood leather jacket", "Black canvas tote"),
            o("Library day", "uni", "Ink pinstripe shirt", "Plaid pleated mini skirt", "Black sheer tights",
              "Black mary janes", "Chocolate corduroy blazer", "Chocolate leather satchel"),
            o("Cold snap", "casual", "Moss mohair jumper", "Black cargo trousers", "Black platform boots",
              "Black wool long coat", "Burgundy wool scarf"),
            o("Dinner", "date", "Plum velvet corset top", "Black tiered maxi skirt", "Black mary janes",
              "Black velvet choker", "Oxblood leather shoulder bag"),
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
