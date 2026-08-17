import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from pydantic import BaseModel, Field

from database import get_db, Review
from services.google_places_client import search_restaurants, get_restaurant_details

router = APIRouter(prefix="/restaurant", tags=["restaurant"])

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", os.getenv("GOOGLE_PLACES_API_KEY"))

# ---------- Schemas ----------

class ReviewSchema(BaseModel):
    id: int
    user_id: str
    place_id: str
    place_name: str
    place_types: Optional[str]
    rating: int
    comment: Optional[str]

    class Config:
        from_attributes = True

class RateRestaurantRequest(BaseModel):
    user_id: str
    place_id: str
    place_name: str
    place_types: Optional[str] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class RecommendationItem(BaseModel):
    id: str
    title: str
    imageUrl: Optional[str]
    reason: str
    score: float
    category: str = "restaurant"


# ---------- Endpoints ----------

@router.get("/search")
def search_restaurants_endpoint(
    query: str = Query(..., min_length=1),
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius: Optional[int] = None
):
    if not GEOAPIFY_API_KEY:
        raise HTTPException(status_code=500, detail="GEOAPIFY_API_KEY is not configured")
        
    results = search_restaurants(query=query, lat=lat, lon=lng)
    
    # We map photo_reference to a usable imageUrl if needed on the frontend, but for now we just return what the client gives
    return {"results": results[:20]}


@router.get("/{place_id}")
def get_restaurant_detail(place_id: str, db: Session = Depends(get_db)):
    if not GEOAPIFY_API_KEY:
        raise HTTPException(status_code=500, detail="GEOAPIFY_API_KEY is not configured")

    details = get_restaurant_details(place_id)
    if not details:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Merge local reviews and average rating
    reviews = db.query(Review).filter(Review.place_id == place_id).all()
    
    local_avg = None
    if reviews:
        total = sum(r.rating for r in reviews)
        local_avg = total / len(reviews)
        
    details["local_reviews"] = [r for r in reviews]
    details["local_avg_rating"] = local_avg
    return details


@router.post("/review")
def review_restaurant(payload: RateRestaurantRequest, db: Session = Depends(get_db)):
    existing = (
        db.query(Review)
        .filter(
            Review.user_id == payload.user_id,
            Review.place_id == payload.place_id
        )
        .first()
    )
    
    if existing:
        existing.place_name = payload.place_name
        if payload.place_types:
            existing.place_types = payload.place_types
        existing.rating = payload.rating
        existing.comment = payload.comment
    else:
        new_review = Review(
            user_id=payload.user_id,
            place_id=payload.place_id,
            place_name=payload.place_name,
            place_types=payload.place_types,
            rating=payload.rating,
            comment=payload.comment
        )
        db.add(new_review)
    
    db.commit()

    return {"message": "Review saved successfully"}


@router.get("/history/{user_id}", response_model=List[ReviewSchema])
def get_history(user_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Review)
        .filter(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
        .all()
    )


@router.get("/recommendations/{user_id}", response_model=List[RecommendationItem])
def get_recommendations(
    user_id: str, 
    lat: Optional[float] = None, 
    lng: Optional[float] = None, 
    db: Session = Depends(get_db), 
    limit: int = 10
):
    if not GEOAPIFY_API_KEY:
        raise HTTPException(status_code=500, detail="GEOAPIFY_API_KEY is not configured")

    # a. Find types user rated >= 4 stars
    high_reviews = (
        db.query(Review)
        .filter(Review.user_id == user_id, Review.rating >= 4)
        .all()
    )
    
    already_reviewed_ids = {
        r.place_id for r in db.query(Review).filter(Review.user_id == user_id).all()
    }

    if not high_reviews:
        # Cold start
        popular = search_restaurants(query="popular restaurant", lat=lat, lon=lng)
        
        candidates = []
        for r in popular:
            if r.get("place_id") in already_reviewed_ids:
                continue
            candidates.append(
                RecommendationItem(
                    id=r.get("place_id"),
                    title=r.get("name"),
                    imageUrl=r.get("photo_reference") if r.get("photo_reference") else None,
                    reason="Popular near you",
                    score=r.get("rating") or 0.0
                )
            )
            if len(candidates) >= limit:
                break
        return candidates

    from collections import defaultdict
    type_weights = defaultdict(float)
    for rev in high_reviews:
        if rev.place_types:
            types = rev.place_types.split(",")
            for t in types:
                t = t.strip()
                if t and t not in ["restaurant", "food", "point_of_interest", "establishment"]:
                    type_weights[t] += rev.rating

    top_types = sorted(type_weights.items(), key=lambda x: x[1], reverse=True)[:3]
    top_type_names = [t[0] for t in top_types]

    query_str = " ".join(top_type_names) if top_type_names else "restaurant"
    search_res = search_restaurants(query=query_str, lat=lat, lon=lng)
    
    candidates = []
    for r in search_res:
        if r.get("place_id") in already_reviewed_ids:
            continue
            
        reason = f"Because you rated {top_type_names[0].replace('_', ' ')} restaurants highly" if top_type_names else "Recommended for you"
        
        candidates.append(
            RecommendationItem(
                id=r.get("place_id"),
                title=r.get("name"),
                imageUrl=r.get("photo_reference") if r.get("photo_reference") else None,
                reason=reason,
                score=r.get("rating") or 0.0
            )
        )
        if len(candidates) >= limit:
            break
            
    return candidates
