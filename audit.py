import os
import sys
import json
import requests
import dotenv

# Load environment variables
dotenv.load_dotenv('.env')

from services.google_places_client import search_restaurants, get_restaurant_details
from services import taste_profile

print("=== STEP 3: LIVE TEST (SEARCH RESTAURANTS) ===")
query = "italian restaurants near New York"
print(f"Executing query: '{query}'")
PLACES_API_BASE_URL = "https://places.googleapis.com/v1"
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

headers = {
    "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
    "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.types,places.priceLevel,places.rating,places.photos",
    "Content-Type": "application/json"
}
payload = {
    "textQuery": query,
    "includedType": "restaurant"
}

print("\n--- RAW JSON REQUEST ---")
print(f"URL: {PLACES_API_BASE_URL}/places:searchText")
print(f"Headers: X-Goog-FieldMask={headers['X-Goog-FieldMask']}")
print(f"Payload: {json.dumps(payload)}")

try:
    response = requests.post(
        f"{PLACES_API_BASE_URL}/places:searchText",
        headers=headers,
        json=payload,
        timeout=8
    )
    print("\n--- RAW JSON RESPONSE (HTTP {}) ---".format(response.status_code))
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error fetching raw response: {e}")

print("\n--- PARSED OUTPUT (from search_restaurants) ---")
parsed = search_restaurants(query)
print(json.dumps(parsed, indent=2))


print("\n\n=== STEP 4: TRACE PREFERENCE DATA (CROSSWALK SCORER) ===")
# We will mock a user who likes two restaurants.
# First, let's search for a couple of specific places to get real IDs, or just use the ones we got above.
if parsed and len(parsed) >= 2:
    place_1 = parsed[0]['place_id']
    place_2 = parsed[1]['place_id']
    name_1 = parsed[0]['name']
    name_2 = parsed[1]['name']
else:
    # fallback to some known IDs or skip
    print("Not enough places returned in search to trace.")
    sys.exit(1)

print(f"Mocking user 'test_user_123' who likes:\n1. {name_1} (ID: {place_1})\n2. {name_2} (ID: {place_2})")

# Mock database.get_likes
original_get_likes = taste_profile.get_likes
def mocked_get_likes(user_id, module):
    if module == "restaurants":
        return [
            {"item_id": place_1},
            {"item_id": place_2}
        ]
    return []
taste_profile.get_likes = mocked_get_likes

# Step 4a: Raw places result for these places
print("\n--- 4a. Raw Places Result for Liked Restaurants ---")
# To get the raw result that _restaurant_cuisine_signal will see, we call get_restaurant_details
details_1 = get_restaurant_details(place_1)
details_2 = get_restaurant_details(place_2)
print(f"Details for {name_1}:")
print(json.dumps(details_1, indent=2))
print(f"Details for {name_2}:")
print(json.dumps(details_2, indent=2))

# Step 4b: Normalized Feature (_restaurant_cuisine_signal)
print("\n--- 4b. Normalized Feature (cuisine signal) ---")
restaurant_signal = taste_profile._restaurant_cuisine_signal("test_user_123")
print(json.dumps(restaurant_signal, indent=2))

# Step 4c: Contribution to unified score (Taste Profile & Boost Map)
print("\n--- 4c. Contribution to Unified Score (Boost Map) ---")
# Let's mock the spotify signal too just to show how it merges, or just rely on restaurants.
# We will just fetch the full taste profile and boost map.
profile = taste_profile.compute_taste_profile("test_user_123")
boost_map = taste_profile.get_restaurant_boost_map("test_user_123")
print("Full Taste Profile Breakdown:")
print(json.dumps(profile["breakdown"], indent=2))
print("Restaurant Numeric Features (Price/Rating):")
print(json.dumps(profile.get("restaurant_features", {}), indent=2))
print("Final Restaurant Boost Map:")
print(json.dumps(boost_map, indent=2))
