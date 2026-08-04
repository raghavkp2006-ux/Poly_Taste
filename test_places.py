import os
from dotenv import load_dotenv
load_dotenv()
from services.google_places_client import search_restaurants
import asyncio

async def test():
    try:
        res = search_restaurants('kfc', lat=12.84, lon=80.15)
        print("Results:")
        print(res)
    except Exception as e:
        print("Error:")
        print(e)

if __name__ == "__main__":
    asyncio.run(test())
