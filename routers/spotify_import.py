"""
routers/spotify_import.py — One-off import endpoint for Spotify streaming history.

POST /spotify/import-history   — runs the full pipeline against a local folder
                                  and stores the resulting taste profile.

This is a SEPARATE import path, not a replacement for the live OAuth flow.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from services.auth import get_current_user_id

router = APIRouter(prefix="/spotify", tags=["spotify-import"])


class ImportRequest(BaseModel):
    history_folder: str
    user_id: Optional[str] = None  # Override; defaults to the logged-in user


@router.post("/import-history")
def import_spotify_history(
    req: ImportRequest,
    current_user_id: str = Depends(get_current_user_id),
):
    """
    Run the full streaming-history import pipeline (Steps 1–6) and store
    the resulting genre profile.

    - ``history_folder``: absolute path to the folder containing
      ``Streaming_History_Audio_*.json`` files.
    - ``user_id`` (optional): override the target user_id. Defaults to the
      currently logged-in user.
    """
    import os

    target_user = req.user_id or current_user_id
    folder = req.history_folder

    if not os.path.isdir(folder):
        raise HTTPException(
            status_code=400,
            detail=f"Folder not found: {folder}",
        )

    # Check that at least one audio history file exists
    audio_files = [
        f for f in os.listdir(folder)
        if f.startswith("Streaming_History_Audio_") and f.endswith(".json")
    ]
    if not audio_files:
        raise HTTPException(
            status_code=400,
            detail="No Streaming_History_Audio_*.json files found in the specified folder.",
        )

    try:
        from scripts.import_spotify_history import run_pipeline

        result = run_pipeline(folder=folder, user_id=target_user, dry_run=False)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Import pipeline failed: {str(e)}",
        )

    return {
        "status": "success",
        "user_id": target_user,
        "total_plays": result["total_plays"],
        "unique_artists": result["unique_artists"],
        "genre_count": len(result["genre_profile"]),
        "top_10_genres": dict(list(result["genre_profile"].items())[:10]),
        "top_5_artists": [
            {"artist": a["artist"], "affinity_score": a["affinity_score"]}
            for a in result["top_artists"][:5]
        ],
    }
