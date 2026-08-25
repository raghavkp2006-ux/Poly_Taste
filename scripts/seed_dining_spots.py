"""
scripts/seed_dining_spots.py — Seed the dining_spots table from the
structured JSON file produced by build_restaurants_cafes.py.

Mirrors scripts/seed_tourist_spots.py in structure and behaviour.
Inserts rows that don't already exist (by place_id); skips duplicates.
"""

import json
import sys
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import get_db, DiningSpot  # noqa: E402


def seed(json_path: Path | None = None) -> None:
    default_json_path = PROJECT_ROOT / "data" / "restaurants_cafes_chennai.json"
    path = json_path or default_json_path

    if not path.exists():
        print(f"ERROR: Data file not found at {path}")
        print("Run scripts/build_restaurants_cafes.py first to generate it.")
        return

    with open(path, "r", encoding="utf-8") as f:
        entries = json.load(f)

    print(f"Loaded {len(entries)} entries from {path.name}")

    db = next(get_db())
    inserted = 0
    skipped = 0

    try:
        for entry in entries:
            existing = db.query(DiningSpot).filter(
                DiningSpot.place_id == entry["place_id"]
            ).first()
            if existing:
                skipped += 1
                continue

            spot = DiningSpot(
                place_id=entry["place_id"],
                name=entry["name"],
                category=entry["category"],
                description=entry.get("description"),
                price_tier=entry.get("price_tier"),
                cuisine=entry.get("cuisine"),
                lat=entry["lat"],
                lng=entry["lng"],
                city=entry.get("city", "Chennai"),
                osm_id=entry.get("osm_id"),
            )
            db.add(spot)
            inserted += 1

        db.commit()
        print(f"Inserted: {inserted} | Skipped (already exist): {skipped}")

        # Verify
        total = db.query(DiningSpot).count()
        print(f"Total dining_spots rows in DB: {total}")

        # Category breakdown
        from sqlalchemy import func as sqlfunc
        cats = db.query(DiningSpot.category, sqlfunc.count()).group_by(DiningSpot.category).all()
        print("Category breakdown in DB:")
        for cat, count in sorted(cats, key=lambda x: -x[1]):
            print(f"  {cat}: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
