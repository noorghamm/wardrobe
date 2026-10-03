import random
from datetime import date, timedelta

import pytest

from wardrobe.db import Repository
from wardrobe.logic import colours, outfits, stats
from wardrobe.models import Item, WearLog
from wardrobe.seed import seed


# ---------- colours ----------
def test_hex_to_hsl_red():
    h, s, l = colours.hex_to_hsl("#ff0000")
    assert h == pytest.approx(0) and s == pytest.approx(1) and l == pytest.approx(0.5)


def test_neutrals_detected():
    assert colours.is_neutral("#1a1a1a")
    assert colours.is_neutral("#f5f5f0")
    assert colours.is_neutral("#8a8a8a")
    assert not colours.is_neutral("#c62828")


def test_pair_scores_order():
    black, white, red, orange, green = "#1a1a1a", "#f5f5f0", "#c62828", "#ef6f5b", "#2f5d3a"
    assert colours.pair_score(black, white) > colours.pair_score(black, black)
    assert colours.pair_score(red, orange) > colours.pair_score(red, green)   # analogous beats triadic
    assert colours.pair_score(red, "#2f4fd1") < colours.pair_score(red, black)  # red/blue clash < neutral


def test_harmony_single_colour_is_one():
    assert colours.harmony(["#c62828"]) == 1.0


def test_nearest_name():
    assert colours.nearest_name("#000000") == "black"
    assert colours.nearest_name("#c62828") == "red"


# ---------- outfits ----------
def _wardrobe():
    repo = Repository(":memory:")
    seed(repo, with_history=False)
    return repo


def test_target_warmth_monotonic():
    temps = [30, 20, 15, 8, 0]
    w = [outfits.target_warmth(t) for t in temps]
    assert w == sorted(w)
    assert w[0] == 1 and w[-1] == 5


def test_generate_returns_complete_outfits():
    repo = _wardrobe()
    sug = outfits.generate(repo.items(), "casual", 15, False, season="autumn", rng=random.Random(0))
    assert sug
    for s in sug:
        cats = {i.category for i in s.items}
        assert "shoes" in cats
        assert ("dress" in cats) or ({"top", "bottom"} <= cats)
        assert 0 <= s.score <= 1


def test_generate_is_deterministic_with_seed():
    repo = _wardrobe()
    a = outfits.generate(repo.items(), "work", 10, False, season="autumn", rng=random.Random(5))
    b = outfits.generate(repo.items(), "work", 10, False, season="autumn", rng=random.Random(5))
    assert [s.item_ids for s in a] == [s.item_ids for s in b]


def test_formal_outfits_are_formal():
    repo = _wardrobe()
    for s in outfits.generate(repo.items(), "formal", 12, False, season="winter", rng=random.Random(1)):
        main = [i for i in s.items if i.category in ("top", "bottom", "dress")]
        assert all(i.formality >= 4 for i in main)


def test_gym_only_uses_gym_tagged_items():
    repo = _wardrobe()
    for s in outfits.generate(repo.items(), "gym", 15, False, season="spring", rng=random.Random(1)):
        assert all("gym" in i.tags or "sport" in i.tags for i in s.items)


def test_cold_rain_adds_outerwear():
    repo = _wardrobe()
    for s in outfits.generate(repo.items(), "casual", 4, True, season="winter", rng=random.Random(3)):
        assert any(i.category == "outerwear" for i in s.items)


def test_laundry_items_excluded():
    repo = _wardrobe()
    for it in repo.items(category="shoes"):
        it.status = "laundry"
        repo.update_item(it)
    assert outfits.generate(repo.items(), "casual", 15, False, season="autumn") == []


def test_pattern_clash_penalised():
    base = dict(category="top", seasons=["autumn"], formality=2, warmth=3)
    a = Item(name="a", colour="#1a1a1a", pattern="stripes", **base)
    b = Item(name="b", category="bottom", colour="#f5f5f0", pattern="check", seasons=["autumn"], formality=2, warmth=3)
    c = Item(name="c", category="bottom", colour="#f5f5f0", pattern="solid", seasons=["autumn"], formality=2, warmth=3)
    sh = Item(name="s", category="shoes", colour="#1a1a1a", seasons=["autumn"], formality=2, warmth=2)
    clash, _ = outfits.score_outfit([a, b, sh], "casual", 12, False)
    clean, _ = outfits.score_outfit([a, c, sh], "casual", 12, False)
    assert clean > clash


# ---------- db ----------
def test_repository_roundtrip(tmp_path):
    repo = Repository(tmp_path / "w.db")
    it = repo.add_item(Item(name="Tee", category="top", subtype="t-shirt", tags=["basic"], price=9.9,
                            purchased=date(2025, 1, 2)))
    assert it.id
    got = repo.get_item(it.id)
    assert got.name == "Tee" and got.tags == ["basic"] and got.purchased == date(2025, 1, 2)
    got.name = "White tee"
    repo.update_item(got)
    assert repo.get_item(it.id).name == "White tee"
    assert repo.items(search="white")[0].id == it.id
    repo.delete_item(it.id)
    assert repo.get_item(it.id) is None


def test_wear_log_and_plan(tmp_path):
    repo = Repository(tmp_path / "w.db")
    seed(repo, with_history=False)
    ids = [i.id for i in repo.items()[:3]]
    repo.log_wear(ids, worn_on=date(2026, 1, 5))
    repo.log_wear(ids[:1], worn_on=date(2026, 1, 9))
    counts = repo.wear_counts()
    assert counts[ids[0]] == 2 and counts[ids[1]] == 1
    assert repo.last_worn()[ids[0]] == date(2026, 1, 9)
    monday = date(2026, 1, 5)
    repo.set_plan(monday, None, "rest day")
    week = repo.plan_for_week(monday)
    assert len(week) == 7 and week[monday].note == "rest day"
    repo.set_plan(monday, None, "changed")
    assert repo.plan_for_week(monday)[monday].note == "changed"   # upsert


def test_seed_is_idempotent():
    repo = Repository(":memory:")
    assert seed(repo) > 0
    assert seed(repo) == 0


# ---------- stats ----------
def test_stats_cost_per_wear_and_never_worn():
    a = Item(id=1, name="coat", category="outerwear", price=200)
    b = Item(id=2, name="tee", category="top", price=10)
    logs = [WearLog(worn_on=date(2026, 1, 1), item_ids=[1]), WearLog(worn_on=date(2026, 1, 8), item_ids=[1])]
    st = stats.item_stats([a, b], logs)
    coat = next(s for s in st if s.item.id == 1)
    assert coat.wears == 2 and coat.cost_per_wear == 100 and coat.last_worn == date(2026, 1, 8)
    assert [s.item.id for s in stats.never_worn(st)] == [2]
    assert stats.most_worn(st)[0].item.id == 1
    assert stats.wardrobe_value([a, b]) == 210
    assert stats.not_worn_since(st, days=30, today=date(2026, 3, 1))[0].item.id == 1
    assert stats.wears_in_period(logs, days=5, today=date(2026, 1, 10)) == 1


# ---------- csv ----------
def test_csv_roundtrip(tmp_path):
    from wardrobe.csvio import export_items, import_items
    repo = Repository(tmp_path / "a.db")
    seed(repo, with_history=False)
    n = export_items(repo, tmp_path / "w.csv")
    repo2 = Repository(tmp_path / "b.db")
    assert import_items(repo2, tmp_path / "w.csv") == n
    a = {(i.name, i.category, i.colour, tuple(i.seasons), tuple(i.tags), i.price) for i in repo.items()}
    b = {(i.name, i.category, i.colour, tuple(i.seasons), tuple(i.tags), i.price) for i in repo2.items()}
    assert a == b


def test_versatility_and_share(tmp_path):
    from wardrobe.share import save_outfit_image
    repo = Repository(":memory:")
    seed(repo, with_history=False)
    v = stats.versatility(repo.items())
    assert v and v[0][1] >= v[-1][1]
    names = [it.name for it, _ in v[:5]]
    assert any(w in n.lower() for n in names for w in ("flares", "tee", "cargo", "turtleneck", "knit"))   # basics rank high
    p = save_outfit_image(repo.items()[:4], "Test outfit", tmp_path / "o.png", "casual")
    assert p.exists() and p.stat().st_size > 1000
