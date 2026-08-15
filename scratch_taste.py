import os
os.environ["USE_LOCAL_DB"] = "true"
from database import SessionLocal, AniListUser
from services.taste_profile import compute_taste_profile

db = SessionLocal()
users = db.query(AniListUser).all()

print(f"Found {len(users)} anilist users.")

for u in users:
    print(f"\nUser: {u.user_id}")
    profile = compute_taste_profile(user_id=u.user_id)
    print(f"Profile dict size: {len(profile['profile'])}")
    print("Top 5 genres:")
    for i, (k, v) in enumerate(profile['profile'].items()):
        if i >= 5: break
        print(f"  {k}: {v}")

db.close()
