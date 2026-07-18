import os
import sys
import requests

# Add parent directory to path so we can import routers.spotify and database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# database exports SessionLocal and SpotifyUser in local-dev mode; they are
# None in Lambda/DynamoDB mode.  The eval script only runs locally so we
# expect the SQLite backend to be active.
from database import SessionLocal, SpotifyUser  # noqa: F401  (imported for side-effect: table creation)

from routers.spotify import (
    compute_genre_profile,
    search_candidates,
    score_candidates,       # online variant: fetches genres via API
    get_artist_genres,
    TEST_USER_ID,
    get_valid_access_token, # signature: (user_id: str) -> str
)


def run_evaluation():
    # get_valid_access_token takes only user_id (no db session needed — the
    # database module now manages its own sessions internally).
    try:
        token = get_valid_access_token(TEST_USER_ID)
    except Exception as e:
        print(f"Error getting token. Ensure you have logged in via /spotify/login. Details: {e}")
        return

    print("Fetching user's top artists...")
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.spotify.com/v1/me/top/artists?limit=50"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch top artists: {response.status_code}")
        return

    artists = response.json().get("items", [])
    if len(artists) < 5:
        print("Not enough top artists to perform leave-one-out evaluation (need at least 5).")
        return

    # We will remove the 3rd top artist (index 2)
    target_index = 2
    removed_artist = artists.pop(target_index)
    removed_id = removed_artist["id"]
    removed_name = removed_artist["name"]

    # Fill in missing genres using the API
    for artist in artists:
        if not artist.get("genres"):
            artist["genres"] = get_artist_genres(artist["id"], token)

    removed_genres = removed_artist.get("genres")
    if not removed_genres:
        removed_genres = get_artist_genres(removed_id, token)

    print(f"\n[EVAL] Removed Artist: {removed_name}")
    print(f"[EVAL] Artist Genres: {removed_genres}\n")

    # Rebuild profile without this artist
    print("Rebuilding genre profile...")
    user_profile = compute_genre_profile(artists)

    sorted_genres = sorted(user_profile.items(), key=lambda item: item[1], reverse=True)
    top_genres = [g for g, score in sorted_genres[:5]]

    print(f"Top 5 Profile Genres: {top_genres}\n")

    print("Searching candidates and scoring...")
    # Passing empty exclusion set for the evaluation to see raw performance
    candidates = search_candidates(top_genres, set(), token)
    scored_tracks = score_candidates(candidates, user_profile, token)

    top_20 = scored_tracks[:20]

    # Check if removed artist appears in top 20
    found_exact = False
    found_related = False

    print("Top 20 Recommendations:")
    for i, track in enumerate(top_20):
        print(f"{i+1}. {track['name']} by {', '.join(track['artists'])} (Score: {track['score']})")
        if removed_name in track["artists"]:
            found_exact = True

        # Check for related artists (sharing 2+ genres)
        if len(set(track.get("matched_genres", [])).intersection(set(removed_genres))) >= 2:
            found_related = True

    print("\n--- Evaluation Results ---")
    if found_exact:
        print("SUCCESS: The removed artist appeared in the top recommendations!")
    else:
        print("MISS: The removed artist did NOT appear in the top recommendations.")

    if found_related:
        print("SUCCESS: Artists sharing 2+ genres with the removed artist appeared in the top recommendations!")
    else:
        print("MISS: No highly related artists appeared.")


if __name__ == "__main__":
    run_evaluation()
