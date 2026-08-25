"""
routers/dining.py — REST endpoints for browsing, filtering, and providing
feedback on dining spots (restaurants & cafes).

Mirrors routers/tourist_spots.py in structure and endpoint conventions.
"""

import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db, get_user
from services.auth import get_current_user_id
from services.taste_profile import compute_taste_profile
from services.dining_spots import get_spots, get_spot_by_id, record_feedback, get_recommendations

router = APIRouter(prefix="/dining", tags=["dining"])


class DiningSpotResponse(BaseModel):
    place_id: str
    name: str
    category: str
    description: Optional[str] = None
    price_tier: Optional[str] = None
    cuisine: Optional[str] = None
    lat: float
    lng: float
    city: str

    model_config = {"from_attributes": True}


class FeedbackRequest(BaseModel):
    rating: int = Field(..., description="Rating must be 1 (like) or -1 (dislike)")
    tag: Optional[str] = None


class FeedbackResponse(BaseModel):
    status: str = "success"
    user_id: str
    place_id: str
    rating: int
    tag: Optional[str] = None


@router.get("", response_model=List[DiningSpotResponse])
def list_dining_spots(
    category: Optional[str] = Query(default=None, description="Filter by dining category"),
    cuisine: Optional[str] = Query(default=None, description="Filter by cuisine substring (e.g. 'indian', 'pizza')"),
    db: Session = Depends(get_db),
):
    """
    List dining spots, optionally filtered by category and/or cuisine.
    Public browsing endpoint — no authentication required.
    """
    return get_spots(db, category=category, cuisine=cuisine)


@router.get("/recommendations", response_model=List[DiningSpotResponse])
def get_dining_recommendations(
    limit: int = Query(default=20, ge=1, le=100, description="Max number of recommendations to return"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get personalized dining spot recommendations for the authenticated user,
    blending their Spotify music and Anime signals via the dining crosswalk,
    with adjustments based on user dining feedback.
    Protected endpoint — requires authentication.
    """
    spotify_token: str | None = None
    try:
        user_record = get_user(user_id)
        if user_record:
            if user_record.get("expires_at", 0) > int(time.time()):
                spotify_token = user_record.get("access_token")
    except Exception:
        pass

    taste_profile = compute_taste_profile(user_id, spotify_token=spotify_token)
    return get_recommendations(db=db, user_id=user_id, taste_profile=taste_profile, limit=limit)


@router.get("/{place_id}", response_model=DiningSpotResponse)
def get_dining_spot(
    place_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve single dining spot detail by place_id.
    Public endpoint — no authentication required.
    """
    spot = get_spot_by_id(db, place_id=place_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dining spot '{place_id}' not found",
        )
    return spot


@router.post("/{place_id}/feedback", status_code=status.HTTP_201_CREATED, response_model=FeedbackResponse)
def post_dining_feedback(
    place_id: str,
    req: FeedbackRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Record user feedback (like/dislike) for a dining spot.
    Protected endpoint — requires authentication.
    """
    if req.rating not in (1, -1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid rating '{req.rating}'. Rating must be 1 or -1.",
        )

    spot = get_spot_by_id(db, place_id=place_id)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dining spot '{place_id}' not found",
        )

    try:
        feedback = record_feedback(
            db=db,
            user_id=user_id,
            place_id=place_id,
            rating=req.rating,
            tag=req.tag,
        )
        return FeedbackResponse(
            status="success",
            user_id=feedback.user_id,
            place_id=feedback.place_id,
            rating=feedback.rating,
            tag=feedback.tag,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
