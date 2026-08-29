import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from database import get_dynamodb_resource, init_db
from routers import google_auth, spotify, spotify_import, anime, taste, anilist, connections, tourist_spots, movie, dining
from services.auth import get_current_user_id, create_session_cookie
from services.spotify_scheduler import start_scheduler, stop_scheduler
from pydantic import BaseModel
from fastapi import HTTPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure database schema and tables are created
    print("[main] Running application startup: initializing database schema...")
    tables = init_db()
    print(f"[main] Database schema verified on startup. Available tables: {tables}")
    # Startup: launch background scheduler
    print("[main] Starting Spotify background scheduler...")
    start_scheduler()
    yield
    # Shutdown: stop scheduler gracefully
    print("[main] Running application shutdown: stopping scheduler...")
    stop_scheduler()


app = FastAPI(title="Multi-Module Recommendation App", lifespan=lifespan)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip("/")
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
allowed_origins = (
    [origin.strip().rstrip("/") for origin in allowed_origins_env.split(",") if origin.strip()]
    if allowed_origins_env
    else list({FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"})
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(google_auth.router)
app.include_router(spotify.router)
app.include_router(spotify_import.router)
app.include_router(anime.router)
app.include_router(movie.router)
app.include_router(taste.router)
app.include_router(anilist.router)
app.include_router(connections.router)
app.include_router(tourist_spots.router)
app.include_router(dining.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Recommendation App API! Visit /docs for Swagger UI"}

@app.get("/auth/me")
def get_me(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id}

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/login")
def login(req: LoginRequest, response: Response):
    if req.email and req.password:
        session_cookie = create_session_cookie(user_id=req.email)
        response.set_cookie(
            key="session",
            value=session_cookie,
            httponly=True,
            samesite="none",
            secure=True,
            path="/",
            max_age=30 * 24 * 60 * 60
        )
        return {"message": "Login successful", "user_id": req.email}
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password. Please try again.")

@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(key="session", path="/", httponly=True, samesite="none", secure=True)
    return {"message": "Logged out successfully"}

@app.get("/api/activity")
def get_activity():
    return []

@app.get("/api/recent")
def get_recent():
    return []

@app.get("/api/recommendations")
def get_recommendations(category: str | None = None):
    return []

@app.get("/debug/counts")
def debug_counts():
    from sqlalchemy.orm import Session
    from sqlalchemy import func
    from database import (
        SessionLocal,
        User,
        SpotifyUser,
        SpotifyPlayEvent,
        UserLike,
        AniListUser,
        SpotifyImportProfile,
        TouristSpot,
        UserSpotFeedback,
        DiningSpot,
        UserDiningFeedback,
        Movie,
    )
    db: Session = SessionLocal()
    try:
        per_user_events = (
            db.query(SpotifyPlayEvent.user_id, func.count(SpotifyPlayEvent.id))
            .group_by(SpotifyPlayEvent.user_id)
            .all()
        )
        users = db.query(User).all()
        spotify_users = db.query(SpotifyUser).all()
        anilist_users = db.query(AniListUser).all()
        import_profiles = db.query(SpotifyImportProfile).all()

        return {
            "counts": {
                "users": db.query(User).count(),
                "spotify_users": db.query(SpotifyUser).count(),
                "spotify_play_events": db.query(SpotifyPlayEvent).count(),
                "user_likes": db.query(UserLike).count(),
                "anilist_users": db.query(AniListUser).count(),
                "spotify_import_profiles": db.query(SpotifyImportProfile).count(),
                "tourist_spots": db.query(TouristSpot).count(),
                "user_spot_feedback": db.query(UserSpotFeedback).count(),
                "dining_spots": db.query(DiningSpot).count(),
                "user_dining_feedback": db.query(UserDiningFeedback).count(),
                "movies": db.query(Movie).count(),
            },
            "play_events_per_user": [{"user_id": u, "count": c} for u, c in per_user_events],
            "users": [
                {"id": u.id, "google_sub": u.google_sub, "email": u.email, "name": u.name}
                for u in users
            ],
            "spotify_users": [
                {
                    "user_id": s.user_id,
                    "spotify_account_id": s.spotify_account_id,
                    "spotify_display_name": s.spotify_display_name,
                    "sync_enabled": s.sync_enabled,
                    "last_synced_at": s.last_synced_at.isoformat() if s.last_synced_at else None,
                }
                for s in spotify_users
            ],
            "anilist_users": [
                {
                    "user_id": a.user_id,
                    "anilist_id": a.anilist_id,
                    "anilist_username": a.anilist_username,
                }
                for a in anilist_users
            ],
            "spotify_import_profiles": [
                {
                    "user_id": p.user_id,
                    "total_plays": p.total_plays,
                    "unique_artists": p.unique_artists,
                }
                for p in import_profiles
            ],
        }
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
