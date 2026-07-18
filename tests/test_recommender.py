import pytest
from routers.spotify import compute_genre_profile, score_candidate_tracks, normalize_genres

def test_normalize_genres():
    # Test bucket matching
    raw = ["chamber psych", "shiver pop", "ambient", "indie rock"]
    norm = normalize_genres(raw)
    # "chamber psych" -> "psych" (wait, psych wasn't in my broad categories list, but "indie" was. Let's check my list: "rock", "metal", "pop", "hip hop", "rap", "jazz", "classical", "electronic", "indie", "folk", "country", "r&b")
    # "shiver pop" -> "pop"
    # "ambient" -> no match in broad categories (so it just stays as "ambient")
    # "indie rock" -> "indie", "rock"
    
    assert "pop" in norm
    assert "rock" in norm
    assert "indie" in norm
    assert "ambient" in norm
    assert "chamber psych" in norm

def test_compute_genre_profile_weighting():
    artists = [
        {"id": "1", "genres": ["pop"]},
        {"id": "2", "genres": ["rock"]},
        {"id": "3", "genres": ["pop", "indie"]}
    ]
    # Total = 3
    # index 0: weight = (3-0)/3 = 1.0 (pop)
    # index 1: weight = (3-1)/3 = 0.66 (rock)
    # index 2: weight = (3-2)/3 = 0.33 (pop, indie)
    # Expected: pop: 1.33, rock: 0.66, indie: 0.33
    
    profile = compute_genre_profile(artists)
    
    # Check normalized keys exist (e.g. pop, rock, indie)
    assert round(profile["pop"], 2) == 1.33
    assert round(profile["rock"], 2) == 0.67 # due to float precision it's 2/3
    assert round(profile["indie"], 2) == 0.33

def test_compute_genre_profile_empty():
    assert compute_genre_profile([]) == {}

def test_score_candidate_tracks():
    user_profile = {"pop": 1.5, "rock": 0.8, "indie": 0.3}
    
    candidates = [
        {"id": "t1", "name": "Pop Song", "artists": [{"name": "A1"}]},
        {"id": "t2", "name": "Rock Song", "artists": [{"name": "A2"}]},
        {"id": "t3", "name": "No Match Song", "artists": [{"name": "A3"}]}
    ]
    
    track_genres_map = {
        "t1": ["pop", "indie"],
        "t2": ["rock"],
        "t3": ["classical"]
    }
    
    scored = score_candidate_tracks(candidates, user_profile, track_genres_map)
    
    # Should only return t1 and t2 (t3 score is 0)
    assert len(scored) == 2
    
    # t1 score: 1.5 + 0.3 = 1.8
    # t2 score: 0.8
    assert scored[0]["id"] == "t1"
    assert scored[0]["score"] == 1.8
    
    assert scored[1]["id"] == "t2"
    assert scored[1]["score"] == 0.8
