import os
from dotenv import load_dotenv
load_dotenv()
from services.google_places_client import search_restaurants, get_restaurant_details
import asyncio

async def test():
    print("--- Test 1: Category Search (Restaurant) near Donauwörth, Germany ---")
    res1 = search_restaurants('restaurant', lat=48.75515, lon=10.71646)
    print(f"Found {len(res1)} results:")
    for r in res1[:3]:
        print(r)
        
    print("\n--- Test 2: Brand Text Search (KFC) ---")
    res2 = search_restaurants('KFC', location='Chennai')
    print(f"Found {len(res2)} results:")
    for r in res2[:3]:
        print(r)

    if res1:
        place_id = res1[0]['place_id']
        print(f"\n--- Test 3: Get Details for {place_id} ---")
        details = get_restaurant_details(place_id)
        print(details)

if __name__ == "__main__":
    asyncio.run(test())
