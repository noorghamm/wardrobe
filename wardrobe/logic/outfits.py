"""Outfit generation: filter the wardrobe by occasion/weather, combine, score, rank."""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from datetime import date

from ..models import Item
from .colours import harmony

# formality ranges per occasion (inclusive)
OCCASION_FORMALITY = {
    "casual": (1, 3), "uni": (1, 3), "travel": (1, 3), "gym": (1, 1),
    "work": (3, 4), "date": (2, 4), "party": (3, 5), "formal": (4, 5),
}


@dataclass
class Suggestion:
    items: list[Item]
    score: float
    reasons: list[str]

    @property
    def item_ids(self) -> list[int]:
        return [i.id for i in self.items if i.id is not None]


def season_for(d: date | None = None) -> str:
    m = (d or date.today()).month
    return {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
            6: "summer", 7: "summer", 8: "summer"}.get(m, "autumn")


def target_warmth(temp_c: float) -> int:
    if temp_c >= 24:
        return 1
    if temp_c >= 18:
        return 2
    if temp_c >= 12:
        return 3
    if temp_c >= 5:
        return 4
    return 5


def needs_outerwear(temp_c: float, rain: bool) -> bool:
    return temp_c < 15 or rain


def _eligible(items: list[Item], occasion: str, season: str, status_ok=("clean",)) -> list[Item]:
    lo, hi = OCCASION_FORMALITY.get(occasion, (1, 5))
    out = []
    for it in items:
        if it.status not in status_ok:
            continue
        if season not in it.seasons:
            continue
        slack = 0 if it.category in ("top", "bottom", "dress", "outerwear") else 1
        if not (lo - slack <= it.formality <= hi + slack):   # main layers strict; shoes/bags get a step
            continue
        sporty = "gym" in it.tags or "sport" in it.tags
        if occasion == "gym" and not sporty:
            continue
        if occasion != "gym" and sporty and not (it.category == "shoes" and occasion in ("casual", "travel")):
            continue      # gym kit stays in the gym bag (trainers are fine for casual days)
        if occasion not in ("casual", "travel") and "lounge" in it.tags:
            continue
        out.append(it)
    return out


def score_outfit(items: list[Item], occasion: str, temp_c: float, rain: bool,
                 wear_counts: dict[int, int] | None = None) -> tuple[float, list[str]]:
    """Score 0..1 with human-readable reasons."""
    reasons: list[str] = []
    wear_counts = wear_counts or {}
    lo, hi = OCCASION_FORMALITY.get(occasion, (1, 5))

    # 1. colour harmony (40%)
    col = harmony([i.colour for i in items])
    reasons.append(f"colour harmony {col:.0%}")

    # 2. formality fit (25%)
    avg_f = sum(i.formality for i in items) / len(items)
    if lo <= avg_f <= hi:
        form = 1.0
    else:
        form = max(0.0, 1.0 - 0.35 * (lo - avg_f if avg_f < lo else avg_f - hi))
    spread = max(i.formality for i in items) - min(i.formality for i in items)
    if spread >= 3:
        form *= 0.7
        reasons.append("mixed formality")
    else:
        reasons.append("formality suits the occasion" if form == 1 else "slightly off the dress code")

    # 3. warmth vs weather (20%) — judged on the main layers, not shoes/bags
    tw = target_warmth(temp_c)
    layers = [i for i in items if i.category in ("top", "bottom", "dress", "outerwear")]
    outfit_w = max(i.warmth for i in layers) if layers else tw
    diff = abs(outfit_w - tw)
    warm = max(0.0, 1.0 - 0.3 * diff)
    if needs_outerwear(temp_c, rain) and temp_c < 10 and not any(i.category == "outerwear" for i in items):
        warm *= 0.6
        reasons.append("needs a coat")
    if diff == 0:
        reasons.append(f"right for {temp_c:.0f}°C")
    elif outfit_w > tw:
        reasons.append("might be warm")
    else:
        reasons.append("might be chilly")
    if rain and not any(i.category == "outerwear" for i in items):
        warm *= 0.7
        reasons.append("no jacket for the rain")
    if rain and any(i.subtype in ("sandals", "heels") for i in items):
        warm *= 0.8
        reasons.append("open shoes in rain")

    # 4. patterns (10%) — one statement pattern is good, two clash
    patterned = [i for i in items if i.pattern != "solid"]
    pat = 1.0 if len(patterned) <= 1 else 0.5
    if len(patterned) > 1:
        reasons.append("pattern clash")

    # 5. freshness (5%) — nudge towards less-worn pieces
    worn = [wear_counts.get(i.id, 0) for i in items]
    fresh = 1.0 / (1.0 + (sum(worn) / len(worn)) / 5.0)

    score = 0.40 * col + 0.25 * form + 0.20 * warm + 0.10 * pat + 0.05 * fresh
    return round(score, 3), reasons


def generate(items: list[Item], occasion: str = "casual", temp_c: float = 15.0, rain: bool = False,
             season: str | None = None, wear_counts: dict[int, int] | None = None,
             n: int = 3, rng: random.Random | None = None, max_candidates: int = 400) -> list[Suggestion]:
    """Return up to n ranked outfit suggestions. Deterministic when given a seeded rng."""
    rng = rng or random.Random()
    season = season or season_for()
    pool = _eligible(items, occasion, season)
    by = {c: [i for i in pool if i.category == c] for c in
          ("top", "bottom", "dress", "outerwear", "shoes", "bag", "accessory")}
    if not by["shoes"]:
        return []

    outer_needed = needs_outerwear(temp_c, rain)
    outer_opts: list[Item | None] = list(by["outerwear"]) if by["outerwear"] else [None]
    if not outer_needed:
        outer_opts = [None] + list(by["outerwear"])[:2]

    bases: list[list[Item]] = []
    for d in by["dress"]:
        bases.append([d])
    for t, b in itertools.product(by["top"], by["bottom"]):
        bases.append([t, b])
    rng.shuffle(bases)
    bases = bases[:max_candidates]

    candidates: list[Suggestion] = []
    for base in bases:
        shoes = rng.sample(by["shoes"], min(2, len(by["shoes"])))
        for sh in shoes:
            for outer in outer_opts[:3]:
                items_ = base + [sh] + ([outer] if outer else [])
                # optional bag / accessory: add if it doesn't hurt the colour story
                extras = []
                if by["bag"]:
                    extras.append(rng.choice(by["bag"]))
                if by["accessory"] and rng.random() < 0.5:
                    extras.append(rng.choice(by["accessory"]))
                best_items = items_
                best_sc, best_reasons = score_outfit(items_, occasion, temp_c, rain, wear_counts)
                for e in extras:
                    sc, rs = score_outfit(best_items + [e], occasion, temp_c, rain, wear_counts)
                    if sc >= best_sc - 0.02:
                        best_items, best_sc, best_reasons = best_items + [e], sc, rs
                candidates.append(Suggestion(best_items, best_sc, best_reasons))

    # rank, then prefer variety: each pick should share no main layer with earlier picks
    ordered = sorted(candidates, key=lambda s: s.score, reverse=True)
    ranked: list[Suggestion] = []
    used: set[int] = set()
    for strict in (True, False):
        for s in ordered:
            if len(ranked) >= n:
                break
            mains = {i.id for i in s.items if i.category in ("top", "bottom", "dress")}
            if s in ranked or (strict and mains & used):
                continue
            if not strict and any(mains == {i.id for i in r.items if i.category in ("top", "bottom", "dress")}
                                  for r in ranked):
                continue
            ranked.append(s)
            used |= mains
    return ranked


def outfit_name(items: list[Item], occasion: str) -> str:
    main = [i for i in items if i.category in ("dress", "top")]
    bottom = [i for i in items if i.category == "bottom"]
    bits = [main[0].name] if main else []
    if bottom:
        bits.append(bottom[0].name)
    return f"{occasion.title()}: " + " + ".join(bits) if bits else f"{occasion.title()} outfit"
