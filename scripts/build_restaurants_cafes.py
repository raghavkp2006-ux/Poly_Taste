"""
scripts/build_restaurants_cafes.py — One-off data ingestion script.

Parses the raw Overpass API GeoJSON export of Chennai restaurants & cafes,
filters unnamed entries, deduplicates, categorizes into six dining categories,
and writes the final structured dataset to data/restaurants_cafes_chennai.json.

This is PLACEHOLDER/BOOTSTRAP data sourced from OpenStreetMap, not curated
hand-written entries. Descriptions and price tiers are NOT available in the
OSM data and are set to null.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Category classification heuristics
# ---------------------------------------------------------------------------

# Cuisine tags that signal dessert/bakery
DESSERT_CUISINES: Set[str] = {
    "ice_cream", "dessert", "pastry", "cake", "bakery", "chocolate",
    "frozen_yogurt", "gelato", "waffle", "crepe",
}

# Cuisine tags that signal street food / quick bite
STREET_FOOD_CUISINES: Set[str] = {
    "fast_food", "burger", "sandwich", "fried_chicken", "kebab",
    "dosa", "chaat", "shawarma", "wrap", "hotdog", "falafel",
    "vada", "pani_puri",
}

# Cuisine tags that signal cafe/coffee
CAFE_CUISINES: Set[str] = {
    "coffee_shop", "coffee", "tea", "bubble_tea",
}

# Cuisine tags that lean fine dining (when combined with brand/hotel signals)
FINE_DINING_CUISINES: Set[str] = {
    "french", "mediterranean", "fine_dining", "european",
}

# Cuisine tags that signal bar/nightlife dining
BAR_CUISINES: Set[str] = {
    "bar", "pub", "brewery", "cocktail",
}

# Name patterns that suggest bar/nightlife
BAR_NAME_PATTERNS = re.compile(
    r"\b(bar|pub|brewery|taproom|lounge|nightclub)\b", re.IGNORECASE
)

# Known fine-dining / hotel restaurant brand patterns
FINE_DINING_NAMES = re.compile(
    r"\b(the\s+great\s+kabab|peshawri|dakshin|avartana|jamavar|"
    r"le\s+dupliex|mgm\s+grand|taj|itc|oberoi|leela|marriott|"
    r"hilton|hyatt|sheraton|radisson|westin|park\s+hyatt|ritz)\b",
    re.IGNORECASE,
)

# Juice/tea stalls (cafes that are really quick-bite)
JUICE_TEA_CUISINES: Set[str] = {"juice", "smoothie"}


def _parse_cuisine_tags(raw: str) -> List[str]:
    """Split semicolon/comma-separated cuisine string into normalized tags."""
    if not raw:
        return []
    # OSM uses semicolons, but some entries use commas
    parts = re.split(r"[;,]", raw)
    return [p.strip().lower().replace(" ", "_") for p in parts if p.strip()]


def _classify(amenity: str, cuisine_tags: List[str], name: str) -> str:
    """Assign a dining category based on amenity type, cuisine tags, and name."""

    tag_set = set(cuisine_tags)

    # 1. Dessert / Bakery — check first (overrides cafe)
    if tag_set & DESSERT_CUISINES:
        return "dessert_bakery"

    # 2. Bar / Nightlife
    if tag_set & BAR_CUISINES or BAR_NAME_PATTERNS.search(name):
        return "bar_nightlife_dining"

    # 3. Street food / Quick bite
    if tag_set & STREET_FOOD_CUISINES:
        return "street_food_quick_bite"
    # Juice/tea stalls in cafe amenity → street food
    if amenity == "cafe" and tag_set & JUICE_TEA_CUISINES:
        return "street_food_quick_bite"

    # 4. Fine dining — brand/hotel name pattern OR fine-dining cuisines
    if FINE_DINING_NAMES.search(name):
        return "fine_dining"
    if tag_set & FINE_DINING_CUISINES:
        return "fine_dining"

    # 5. Cafe / Coffee — ALL amenity=cafe entries map here, regardless of
    #    cuisine tag.  If a cafe serves meals (indian, italian, etc.) it's
    #    still a cafe.  Only dessert/bar/street-food cuisine checks above
    #    can override this.
    if amenity == "cafe":
        return "cafe_coffee"

    # 6. Default for restaurants without clear signals
    return "casual_dining"


def _make_place_id(name: str, osm_id: str) -> str:
    """Generate a URL-friendly place_id from the name, with OSM ID suffix for uniqueness."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    # Use last part of OSM ID (e.g., "node/12345" → "12345") for uniqueness
    id_suffix = osm_id.split("/")[-1] if "/" in osm_id else osm_id
    return f"{slug}-{id_suffix}"


def build() -> None:
    """Main ingestion pipeline."""

    # --- Locate the export file ---
    export_path = PROJECT_ROOT / "export (2).geojson"
    if not export_path.exists():
        print(f"ERROR: Export file not found at {export_path}")
        return

    with open(export_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    print(f"Total features in export: {len(features)}")

    # --- Step 1: Filter unnamed entries ---
    named = [f for f in features if f.get("properties", {}).get("name")]
    unnamed_count = len(features) - len(named)
    print(f"Dropped {unnamed_count} unnamed entries")
    print(f"Named entries remaining: {len(named)}")

    # --- Step 2: Deduplicate on (name_lower, rounded_coords) ---
    seen: Set[Tuple[str, float, float]] = set()
    deduped: List[Dict[str, Any]] = []
    dup_count = 0

    for feat in named:
        props = feat["properties"]
        name = props["name"].strip()
        coords = feat["geometry"]["coordinates"]  # [lon, lat] in GeoJSON
        lon, lat = coords[0], coords[1]

        # Round to ~11m precision for dedup
        key = (name.lower(), round(lat, 4), round(lon, 4))
        if key in seen:
            dup_count += 1
            continue
        seen.add(key)
        deduped.append(feat)

    print(f"Removed {dup_count} duplicates")
    print(f"Entries after dedup: {len(deduped)}")

    # --- Step 3: Extract fields + categorize ---
    results: List[Dict[str, Any]] = []
    category_counts: Dict[str, int] = {}

    for feat in deduped:
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]  # [lon, lat]

        name = props["name"].strip()
        amenity = props.get("amenity", "restaurant")
        osm_id = props.get("@id", "")
        cuisine_raw = props.get("cuisine", "")
        cuisine_tags = _parse_cuisine_tags(cuisine_raw)

        # Swap GeoJSON [lon, lat] → project's lat, lng
        lat = coords[1]
        lng = coords[0]

        category = _classify(amenity, cuisine_tags, name)
        category_counts[category] = category_counts.get(category, 0) + 1

        entry: Dict[str, Any] = {
            "place_id": _make_place_id(name, osm_id),
            "name": name,
            "category": category,
            "description": None,  # Not available in OSM data
            "price_tier": None,   # Not available in OSM data
            "cuisine": cuisine_raw if cuisine_raw else None,
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "city": "Chennai",
            "osm_id": osm_id,
        }

        # Extract optional useful tags
        for optional_key in ("opening_hours", "brand", "website", "phone",
                             "addr:street", "addr:city", "addr:postcode"):
            val = props.get(optional_key)
            if val:
                entry[optional_key.replace(":", "_")] = val

        results.append(entry)

    # --- Step 4: Write output ---
    out_path = PROJECT_ROOT / "data" / "restaurants_cafes_chennai.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(results)} entries to {out_path}")
    print(f"\nCategory breakdown:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    build()
