import json
data = json.load(open('data/raw/anime_catalog.json', 'r'))
print(f"catalog entries: {len(data)}")
if data:
    print(f"first entry keys: {list(data[0].keys())}")
    print(f"first title: {data[0].get('title', '?')}")
    print(f"has synopsis: {'synopsis' in data[0]}")
    print(f"has genres: {'genres' in data[0]}")
    print(f"genres type: {type(data[0].get('genres', []))}")
    print(f"first genres: {data[0].get('genres', [])}")
else:
    print("EMPTY")
