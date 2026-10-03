"""SQLite persistence. One small repository class; the UI never touches SQL."""
from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from . import DB_PATH
from .models import CATEGORIES, Item, Outfit, PlanEntry, WearLog

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subtype TEXT DEFAULT '',
    colour TEXT DEFAULT '#808080',
    colour_name TEXT DEFAULT 'grey',
    pattern TEXT DEFAULT 'solid',
    seasons TEXT DEFAULT '["spring","summer","autumn","winter"]',
    formality INTEGER DEFAULT 3,
    warmth INTEGER DEFAULT 3,
    brand TEXT DEFAULT '',
    price REAL DEFAULT 0,
    purchased TEXT,
    image_path TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    tags TEXT DEFAULT '[]',
    status TEXT DEFAULT 'clean',
    favourite INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS outfits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    item_ids TEXT NOT NULL,
    occasion TEXT DEFAULT 'casual',
    notes TEXT DEFAULT '',
    score REAL DEFAULT 0,
    created TEXT
);
CREATE TABLE IF NOT EXISTS wear_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worn_on TEXT NOT NULL,
    item_ids TEXT NOT NULL,
    outfit_id INTEGER,
    note TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL UNIQUE,
    outfit_id INTEGER,
    note TEXT DEFAULT ''
);
"""


def _d(s: str | None) -> date | None:
    return date.fromisoformat(s) if s else None


class Repository:
    def __init__(self, path: Path | str = DB_PATH):
        self.path = Path(path)
        if str(path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    # ---------- items ----------
    def _row_to_item(self, r: sqlite3.Row) -> Item:
        return Item(
            id=r["id"], name=r["name"], category=r["category"], subtype=r["subtype"],
            colour=r["colour"], colour_name=r["colour_name"], pattern=r["pattern"],
            seasons=json.loads(r["seasons"]), formality=r["formality"], warmth=r["warmth"],
            brand=r["brand"], price=r["price"], purchased=_d(r["purchased"]),
            image_path=r["image_path"], notes=r["notes"], tags=json.loads(r["tags"]),
            status=r["status"], favourite=bool(r["favourite"]),
        )

    def add_item(self, it: Item) -> Item:
        cur = self.conn.execute(
            """INSERT INTO items (name,category,subtype,colour,colour_name,pattern,seasons,formality,
               warmth,brand,price,purchased,image_path,notes,tags,status,favourite)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (it.name, it.category, it.subtype, it.colour, it.colour_name, it.pattern,
             json.dumps(it.seasons), it.formality, it.warmth, it.brand, it.price,
             it.purchased.isoformat() if it.purchased else None, it.image_path, it.notes,
             json.dumps(it.tags), it.status, int(it.favourite)),
        )
        self.conn.commit()
        it.id = cur.lastrowid
        return it

    def update_item(self, it: Item) -> None:
        self.conn.execute(
            """UPDATE items SET name=?,category=?,subtype=?,colour=?,colour_name=?,pattern=?,seasons=?,
               formality=?,warmth=?,brand=?,price=?,purchased=?,image_path=?,notes=?,tags=?,status=?,favourite=?
               WHERE id=?""",
            (it.name, it.category, it.subtype, it.colour, it.colour_name, it.pattern,
             json.dumps(it.seasons), it.formality, it.warmth, it.brand, it.price,
             it.purchased.isoformat() if it.purchased else None, it.image_path, it.notes,
             json.dumps(it.tags), it.status, int(it.favourite), it.id),
        )
        self.conn.commit()

    def delete_item(self, item_id: int) -> None:
        self.conn.execute("DELETE FROM items WHERE id=?", (item_id,))
        self.conn.commit()

    def get_item(self, item_id: int) -> Item | None:
        r = self.conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        return self._row_to_item(r) if r else None

    def items(self, category: str | None = None, season: str | None = None,
              search: str = "", status: str | None = None, favourites_only: bool = False) -> list[Item]:
        rows = self.conn.execute("SELECT * FROM items ORDER BY name").fetchall()
        order = {c: k for k, c in enumerate(CATEGORIES)}
        out = sorted((self._row_to_item(r) for r in rows), key=lambda i: (order.get(i.category, 99), i.name))
        if category and category != "all":
            out = [i for i in out if i.category == category]
        if season and season != "all":
            out = [i for i in out if season in i.seasons]
        if status and status != "all":
            out = [i for i in out if i.status == status]
        if favourites_only:
            out = [i for i in out if i.favourite]
        if search:
            s = search.lower()
            out = [i for i in out if s in i.name.lower() or s in i.brand.lower()
                   or s in i.colour_name.lower() or s in i.subtype.lower()
                   or any(s in t.lower() for t in i.tags)]
        return out

    def count_items(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]

    # ---------- outfits ----------
    def _row_to_outfit(self, r: sqlite3.Row) -> Outfit:
        return Outfit(id=r["id"], name=r["name"], item_ids=json.loads(r["item_ids"]),
                      occasion=r["occasion"], notes=r["notes"], score=r["score"],
                      created=_d(r["created"]) or date.today())

    def add_outfit(self, o: Outfit) -> Outfit:
        cur = self.conn.execute(
            "INSERT INTO outfits (name,item_ids,occasion,notes,score,created) VALUES (?,?,?,?,?,?)",
            (o.name, json.dumps(o.item_ids), o.occasion, o.notes, o.score, o.created.isoformat()))
        self.conn.commit()
        o.id = cur.lastrowid
        return o

    def update_outfit(self, o: Outfit) -> None:
        self.conn.execute("UPDATE outfits SET name=?,item_ids=?,occasion=?,notes=?,score=? WHERE id=?",
                          (o.name, json.dumps(o.item_ids), o.occasion, o.notes, o.score, o.id))
        self.conn.commit()

    def delete_outfit(self, outfit_id: int) -> None:
        self.conn.execute("DELETE FROM outfits WHERE id=?", (outfit_id,))
        self.conn.execute("UPDATE plan SET outfit_id=NULL WHERE outfit_id=?", (outfit_id,))
        self.conn.commit()

    def get_outfit(self, outfit_id: int) -> Outfit | None:
        r = self.conn.execute("SELECT * FROM outfits WHERE id=?", (outfit_id,)).fetchone()
        return self._row_to_outfit(r) if r else None

    def outfits(self) -> list[Outfit]:
        return [self._row_to_outfit(r) for r in
                self.conn.execute("SELECT * FROM outfits ORDER BY created DESC, id DESC")]

    # ---------- wear log ----------
    def log_wear(self, item_ids: list[int], outfit_id: int | None = None,
                 worn_on: date | None = None, note: str = "") -> WearLog:
        worn_on = worn_on or date.today()
        cur = self.conn.execute(
            "INSERT INTO wear_log (worn_on,item_ids,outfit_id,note) VALUES (?,?,?,?)",
            (worn_on.isoformat(), json.dumps(item_ids), outfit_id, note))
        self.conn.commit()
        return WearLog(id=cur.lastrowid, worn_on=worn_on, item_ids=item_ids, outfit_id=outfit_id, note=note)

    def wear_log(self, since: date | None = None) -> list[WearLog]:
        q = "SELECT * FROM wear_log"
        args: tuple = ()
        if since:
            q += " WHERE worn_on >= ?"
            args = (since.isoformat(),)
        q += " ORDER BY worn_on DESC, id DESC"
        return [WearLog(id=r["id"], worn_on=date.fromisoformat(r["worn_on"]),
                        item_ids=json.loads(r["item_ids"]), outfit_id=r["outfit_id"], note=r["note"])
                for r in self.conn.execute(q, args)]

    def wear_counts(self) -> dict[int, int]:
        counts: dict[int, int] = {}
        for log in self.wear_log():
            for i in log.item_ids:
                counts[i] = counts.get(i, 0) + 1
        return counts

    def last_worn(self) -> dict[int, date]:
        last: dict[int, date] = {}
        for log in self.wear_log():          # newest first
            for i in log.item_ids:
                last.setdefault(i, log.worn_on)
        return last

    # ---------- planner ----------
    def plan_for_week(self, monday: date) -> dict[date, PlanEntry]:
        out: dict[date, PlanEntry] = {}
        for k in range(7):
            d = monday + timedelta(days=k)
            r = self.conn.execute("SELECT * FROM plan WHERE day=?", (d.isoformat(),)).fetchone()
            out[d] = PlanEntry(id=r["id"], day=d, outfit_id=r["outfit_id"], note=r["note"]) if r \
                else PlanEntry(day=d, outfit_id=None)
        return out

    def set_plan(self, day: date, outfit_id: int | None, note: str = "") -> None:
        self.conn.execute(
            "INSERT INTO plan (day,outfit_id,note) VALUES (?,?,?) "
            "ON CONFLICT(day) DO UPDATE SET outfit_id=excluded.outfit_id, note=excluded.note",
            (day.isoformat(), outfit_id, note))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
