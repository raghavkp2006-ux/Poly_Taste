"""
scripts/seed_tourist_spots.py

Seed script to populate the 'tourist_spots' table from curated JSON data
(data/tourist_spots_chennai.json) using SQLAlchemy ORM.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from sqlalchemy import func
    from database import SessionLocal, Base, TouristSpot
    try:
        from database import engine
    except ImportError:
        from database import _engine as engine
except ImportError as e:
    print(f"[ERROR] Failed to import database dependencies from database.py: {e}")
    sys.exit(1)


VALID_CATEGORIES = {
    "adventure_outdoor",
    "cultural_historic",
    "nightlife",
    "chill_scenic",
    "shopping_social",
    "offbeat_indie",
}

VALID_PRICE_TIERS = {
    "free",
    "paid",
    "premium",
}

REQUIRED_FIELDS = ["place_id", "name", "category", "price_tier", "lat", "lng", "city"]


def validate_record(record: Dict[str, Any], idx: int) -> Tuple[bool, str]:
    if not isinstance(record, dict):
        return False, f"Record at index {idx} is not a JSON object."

    for field in REQUIRED_FIELDS:
        if field not in record or record[field] is None or str(record[field]).strip() == "":
            return False, f"Record '{record.get('place_id', f'idx:{idx}')}' missing required field: '{field}'."

    category = record.get("category")
    if category not in VALID_CATEGORIES:
        return False, (
            f"Record '{record['place_id']}' has invalid category '{category}'. "
            f"Allowed values: {sorted(VALID_CATEGORIES)}"
        )

    price_tier = record.get("price_tier")
    if price_tier not in VALID_PRICE_TIERS:
        return False, (
            f"Record '{record['place_id']}' has invalid price_tier '{price_tier}'. "
            f"Allowed values: {sorted(VALID_PRICE_TIERS)}"
        )

    try:
        float(record["lat"])
        float(record["lng"])
    except (ValueError, TypeError):
        return False, f"Record '{record['place_id']}' has non-numeric lat/lng values."

    return True, ""


def seed_tourist_spots(json_path: Path) -> None:
    if not json_path.exists():
        print(f"[ERROR] Seed file not found at: {json_path}")
        print("Please ensure 'data/tourist_spots_chennai.json' exists relative to project root.")
        sys.exit(1)

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except json.JSONDecodeError as err:
        print(f"[ERROR] Failed to parse JSON file {json_path}: {err}")
        sys.exit(1)
    except Exception as err:
        print(f"[ERROR] Unexpected error reading {json_path}: {err}")
        sys.exit(1)

    if not isinstance(raw_data, list):
        print(f"[ERROR] Expected JSON root to be a list of spot objects, got {type(raw_data).__name__}.")
        sys.exit(1)

    if engine is not None:
        Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    total_records = len(raw_data)
    inserted_count = 0
    updated_count = 0
    skipped_records: List[Tuple[str, str]] = []

    print(f"\n[INFO] Starting tourist spots database seed...")
    print(f"[INFO] Source file: {json_path} ({total_records} total records)")

    try:
        for idx, item in enumerate(raw_data):
            is_valid, error_msg = validate_record(item, idx)
            if not is_valid:
                print(f"[WARNING] Skipping item {idx}: {error_msg}")
                skipped_records.append((item.get("place_id", f"index_{idx}"), error_msg))
                continue

            place_id = str(item["place_id"]).strip()
            existing_spot = session.query(TouristSpot).filter(TouristSpot.place_id == place_id).first()

            if existing_spot:
                existing_spot.name = str(item["name"]).strip()
                existing_spot.category = str(item["category"]).strip()
                existing_spot.description = str(item.get("description", "")).strip() or None
                existing_spot.price_tier = str(item["price_tier"]).strip()
                existing_spot.lat = float(item["lat"])
                existing_spot.lng = float(item["lng"])
                existing_spot.city = str(item.get("city", "Chennai")).strip()
                updated_count += 1
            else:
                new_spot = TouristSpot(
                    place_id=place_id,
                    name=str(item["name"]).strip(),
                    category=str(item["category"]).strip(),
                    description=str(item.get("description", "")).strip() or None,
                    price_tier=str(item["price_tier"]).strip(),
                    lat=float(item["lat"]),
                    lng=float(item["lng"]),
                    city=str(item.get("city", "Chennai")).strip(),
                )
                session.add(new_spot)
                inserted_count += 1

        session.commit()
        print(f"[SUCCESS] Database transaction committed successfully.")

    except Exception as err:
        session.rollback()
        print(f"[ERROR] Transaction failed and was rolled back: {err}")
        sys.exit(1)
    finally:
        try:
            category_counts = (
                session.query(TouristSpot.category, func.count(TouristSpot.place_id))
                .group_by(TouristSpot.category)
                .all()
            )
            total_in_db = session.query(TouristSpot).count()
        except Exception:
            category_counts = []
            total_in_db = 0
        session.close()

    print("\n" + "=" * 60)
    print("           SEEDING SUMMARY REPORT")
    print("=" * 60)
    print(f" Total records evaluated  : {total_records}")
    print(f" Newly inserted rows      : {inserted_count}")
    print(f" Updated existing rows    : {updated_count}")
    print(f" Skipped / Invalid rows   : {len(skipped_records)}")

    if skipped_records:
        print("\nSkipped Items Breakdown:")
        for pid, reason in skipped_records:
            print(f"  - [{pid}]: {reason}")

    print("\n" + "-" * 60)
    print(f" Current Database State ('tourist_spots' table: {total_in_db} rows)")
    print("-" * 60)
    if category_counts:
        for cat, count in sorted(category_counts, key=lambda x: x[0]):
            print(f"  • {cat:<22} : {count:>3} spots")
    else:
        print("  (Unable to retrieve category counts)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    default_json_path = PROJECT_ROOT / "data" / "tourist_spots_chennai.json"
    seed_tourist_spots(default_json_path)
