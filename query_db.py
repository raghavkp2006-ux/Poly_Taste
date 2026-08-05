from database import SessionLocal, AniListUser, SpotifyUser, User

def query():
    db = SessionLocal()
    try:
        print("--- Spotify Users ---")
        for u in db.query(SpotifyUser).all():
            print(u.user_id)
        print("--- Google Users (User Table) ---")
        for u in db.query(User).all():
            print(u.id, u.email, u.name)
        print("--- AniList Users ---")
        for u in db.query(AniListUser).all():
            print("User ID:", u.user_id)
            print("AniList ID:", u.anilist_id)
            print("Username:", u.anilist_username)
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    query()
