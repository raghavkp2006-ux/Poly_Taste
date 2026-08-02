import torch
import torch.nn as nn
import random

# Import our recommender objects
from services.anime_recommender import get_or_compute_embedding, anime_data_map

def find_by_title(substring):
    for aid, data in anime_data_map.items():
        if substring.lower() in data['title'].lower():
            return aid, data['title']
    return None, None

def get_random():
    aid = random.choice(list(anime_data_map.keys()))
    return aid, anime_data_map[aid]['title']

def main():
    print("--- Cold Start Embedding Semantic Verification ---")
    
    # 1. Find known titles in the dataset
    action_id, action_title = find_by_title("My Hero Academia")
    if not action_id:
        action_id, action_title = find_by_title("Naruto")
        
    romcom_id, romcom_title = find_by_title("Toradora")
    if not romcom_id:
        romcom_id, romcom_title = find_by_title("Kaguya")
        
    random_id1, random_title1 = get_random()
    random_id2, random_title2 = get_random()
    
    print(f"Known Action/Shounen: {action_title} (ID: {action_id})")
    print(f"Known Romcom: {romcom_title} (ID: {romcom_id})")
    print(f"Control 1: {random_title1} (ID: {random_id1})")
    print(f"Control 2: {random_title2} (ID: {random_id2})")
    print("-" * 50)
    
    # 2. Pick new anime (Simulate Cold Start by bypassing AniList network call with raw metadata)
    solo_leveling_meta = {
        "title": "Solo Leveling",
        "description": "They say whatever doesn’t kill you makes you stronger, but that’s not the case for the world’s weakest hunter Sung Jinwoo. After being brutally slaughtered by monsters in a high-ranking dungeon, Jinwoo came back with the System, a program only he could see, that’s leveling him up in every way. Now, he’s inspired to discover the secrets behind his powers and the dungeon that spawned them.",
        "genres": ["Action", "Adventure", "Fantasy"],
        "tags": [{"name": "Magic"}, {"name": "Male Protagonist"}, {"name": "Monsters"}, {"name": "Overpowered Main Character"}]
    }

    dangers_in_my_heart_meta = {
        "title": "The Dangers in My Heart",
        "description": "Fascinated by murder and all things macabre, Kyoutaro daydreams of acting out his twisted fantasies on his unsuspecting classmates — but an encounter with Anna Yamada, the gorgeous class idol, lights a spark in the dark. It’s a classic tale of an antisocial boy falling for a popular girl, but neither are who they appear to be. Will they discover each other’s secret selves?",
        "genres": ["Comedy", "Romance", "Slice of Life"],
        "tags": [{"name": "School"}, {"name": "Tsundere"}, {"name": "Coming of Age"}]
    }
    
    test_cases = [
        (9999991, solo_leveling_meta),
        (9999992, dangers_in_my_heart_meta)
    ]
    
    cos = nn.CosineSimilarity(dim=0, eps=1e-6)
    
    # Convert to tensor
    t_action = torch.tensor(anime_data_map[action_id]['embedding'], dtype=torch.float32)
    t_romcom = torch.tensor(anime_data_map[romcom_id]['embedding'], dtype=torch.float32)
    t_rand1 = torch.tensor(anime_data_map[random_id1]['embedding'], dtype=torch.float32)
    t_rand2 = torch.tensor(anime_data_map[random_id2]['embedding'], dtype=torch.float32)
    
    print("--- Known Dataset Similarities ---")
    print(f"Action vs Romcom: {cos(t_action, t_romcom).item():.4f}")
    print(f"Action vs Random 1: {cos(t_action, t_rand1).item():.4f}")
    print(f"Romcom vs Random 2: {cos(t_romcom, t_rand2).item():.4f}")
    print("-" * 50)
    
    for aid, meta in test_cases:
        desc = meta["title"]
        print(f"\nEvaluating Cold-Start: {desc} (ID: {aid})")
            
        emb, title, genres = get_or_compute_embedding(aid, metadata=meta)
        if emb is None:
            print("  Failed to compute embedding (thin metadata?).")
            continue
            
        print(f"  Fetched successfully: {title} | Genres: {genres}")
        
        # Convert to tensor
        t_emb = torch.tensor(emb, dtype=torch.float32)
        
        t_action = torch.tensor(anime_data_map[action_id]['embedding'], dtype=torch.float32)
        t_romcom = torch.tensor(anime_data_map[romcom_id]['embedding'], dtype=torch.float32)
        t_rand1 = torch.tensor(anime_data_map[random_id1]['embedding'], dtype=torch.float32)
        t_rand2 = torch.tensor(anime_data_map[random_id2]['embedding'], dtype=torch.float32)
        
        print("  Cosine Similarities:")
        print(f"    vs {action_title} (Action): {cos(t_emb, t_action).item():.4f}")
        print(f"    vs {romcom_title} (Romcom): {cos(t_emb, t_romcom).item():.4f}")
        print(f"    vs {random_title1} (Random 1): {cos(t_emb, t_rand1).item():.4f}")
        print(f"    vs {random_title2} (Random 2): {cos(t_emb, t_rand2).item():.4f}")

if __name__ == "__main__":
    main()
