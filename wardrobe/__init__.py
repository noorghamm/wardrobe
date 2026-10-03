"""Wardrobe — a digital wardrobe and outfit planner."""
from pathlib import Path

__version__ = "0.1.0"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
IMAGE_DIR = DATA_DIR / "images"
PLACEHOLDER_DIR = IMAGE_DIR / "placeholders"
USER_IMAGE_DIR = IMAGE_DIR / "user"
DB_PATH = DATA_DIR / "wardrobe.db"
