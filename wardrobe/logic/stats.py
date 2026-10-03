"""Wardrobe statistics used by the Stats view (pure functions, easy to test)."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta

from ..models import Item, WearLog


@dataclass
class ItemStat:
    item: Item
    wears: int
    last_worn: date | None
    cost_per_wear: float | None


def item_stats(items: list[Item], logs: list[WearLog]) -> list[ItemStat]:
    counts: Counter[int] = Counter()
    last: dict[int, date] = {}
    for log in logs:
        for i in log.item_ids:
            counts[i] += 1
            if i not in last or log.worn_on > last[i]:
                last[i] = log.worn_on
    out = []
    for it in items:
        w = counts.get(it.id, 0)
        cpw = (it.price / w) if (it.price and w) else (it.price if it.price else None)
        out.append(ItemStat(it, w, last.get(it.id), cpw))
    return out


def most_worn(stats: list[ItemStat], n: int = 5) -> list[ItemStat]:
    return sorted([s for s in stats if s.wears > 0], key=lambda s: s.wears, reverse=True)[:n]


def never_worn(stats: list[ItemStat]) -> list[ItemStat]:
    return [s for s in stats if s.wears == 0]


def not_worn_since(stats: list[ItemStat], days: int = 90, today: date | None = None) -> list[ItemStat]:
    today = today or date.today()
    cutoff = today - timedelta(days=days)
    return [s for s in stats if s.last_worn and s.last_worn < cutoff]


def colour_breakdown(items: list[Item]) -> list[tuple[str, int]]:
    c = Counter(i.colour_name for i in items)
    return c.most_common()


def category_breakdown(items: list[Item]) -> list[tuple[str, int]]:
    c = Counter(i.category for i in items)
    return c.most_common()


def wears_in_period(logs: list[WearLog], days: int = 30, today: date | None = None) -> int:
    today = today or date.today()
    cutoff = today - timedelta(days=days)
    return sum(1 for log in logs if log.worn_on >= cutoff)


def wardrobe_value(items: list[Item]) -> float:
    return round(sum(i.price for i in items), 2)


def best_value(stats: list[ItemStat], n: int = 5) -> list[ItemStat]:
    """Lowest cost-per-wear among priced, worn items."""
    priced = [s for s in stats if s.cost_per_wear is not None and s.wears > 0]
    return sorted(priced, key=lambda s: s.cost_per_wear)[:n]


def versatility(items: list[Item], threshold: float = 0.8) -> list[tuple[Item, int]]:
    """Capsule analysis: for each main-layer piece, how many other main pieces it pairs with
    (colour harmony above `threshold`, compatible formality, overlapping seasons). Most versatile first."""
    from .colours import pair_score
    mains = [i for i in items if i.category in ("top", "bottom", "dress", "outerwear")]
    out = []
    for a in mains:
        n = 0
        for b in mains:
            if a is b or a.category == b.category:
                continue
            if a.category == "dress" and b.category in ("top", "bottom"):
                continue
            if b.category == "dress" and a.category in ("top", "bottom"):
                continue
            if not set(a.seasons) & set(b.seasons):
                continue
            if abs(a.formality - b.formality) > 1:
                continue
            if pair_score(a.colour, b.colour) >= threshold:
                n += 1
        out.append((a, n))
    return sorted(out, key=lambda t: t[1], reverse=True)
