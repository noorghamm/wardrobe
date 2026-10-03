"""Run with:  python -m wardrobe   (or just `wardrobe` after `pip install -e .`)."""
from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="wardrobe", description="Digital wardrobe and outfit planner")
    ap.add_argument("--db", help="path to the SQLite database (default: data/wardrobe.db in the project)")
    ap.add_argument("--demo", action="store_true", help="load the demo wardrobe if the database is empty")
    ap.add_argument("--reset", action="store_true", help="delete the database first (careful!)")
    args = ap.parse_args(argv)

    from . import DB_PATH
    from pathlib import Path
    db = Path(args.db) if args.db else DB_PATH
    if args.reset and db.exists():
        db.unlink()
    if args.demo:
        from .db import Repository
        from .seed import seed
        repo = Repository(db)
        n = seed(repo)
        repo.close()
        print(f"demo wardrobe: {n} items added" if n else "database already has items; demo not loaded")

    from .ui.app import App
    App(db).mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
