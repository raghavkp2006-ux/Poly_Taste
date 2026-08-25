"""
services/dining_spots.py — Service layer for dining spots (restaurants/cafes)
catalog and user feedback.

Mirrors services/tourist_spots.py in structure and behaviour, adapted for
the dining_spots table and DINING_CROSSWALK.
"""

from typing import List, Optional
from database import DiningSpot, UserDiningFeedback


def get_spots(db, category: str | None = None, cuisine: str | None = None) -> list:
    """
    Return dining spots from the dining_spots table, optionally filtered
    by category and/or cuisine substring.  No personalization, no ranking
    logic — a plain filtered query.
    """
    query = db.query(DiningSpot)
    if category:
        query = query.filter(DiningSpot.category == category)
    if cuisine:
        query = query.filter(DiningSpot.cuisine.ilike(f"%{cuisine}%"))
    return query.all()


def get_spot_by_id(db, place_id: str):
    """Return a single dining spot by place_id, or None if not found."""
    return db.query(DiningSpot).filter(DiningSpot.place_id == place_id).first()


def record_feedback(db, user_id: str, place_id: str, rating: int, tag: str | None = None):
    """
    Insert a row into user_dining_feedback for this user/place.
    rating must be 1 or -1 — validate and raise a clear error otherwise.
    If a feedback row already exists for this user+place, update it
    rather than creating a duplicate (upsert on user_id + place_id).
    """
    if rating not in (1, -1):
        raise ValueError(f"Invalid rating '{rating}'. Rating must be 1 or -1.")

    feedback = (
        db.query(UserDiningFeedback)
        .filter(UserDiningFeedback.user_id == user_id, UserDiningFeedback.place_id == place_id)
        .first()
    )
    if feedback:
        feedback.rating = rating
        feedback.tag = tag
    else:
        feedback = UserDiningFeedback(
            user_id=user_id,
            place_id=place_id,
            rating=rating,
            tag=tag,
        )
        db.add(feedback)

    db.commit()
    db.refresh(feedback)
    return feedback


def get_recommendations(db, user_id: str, taste_profile: dict, limit: int = 20) -> list:
    """
    Rank dining spots using crosswalk_dining category weights from taste_profile.
    Apply a small adjustment per category based on this user's own
    user_dining_feedback history: categories where the user has net-positive
    feedback get a small boost (e.g. up to +10%), net-negative get a small
    penalty (e.g. up to -10%). Cap the adjustment so no single rating swings
    results drastically. Return the top `limit` spots sorted by final score.
    """
    spots = db.query(DiningSpot).all()
    if not spots:
        return []

    crosswalk_dining = {}
    if isinstance(taste_profile, dict):
        crosswalk_dining = taste_profile.get("crosswalk_dining", {}) or {}

    # Map place_id -> spot for quick category lookup
    spot_by_id = {s.place_id: s for s in spots}

    # Gather user's dining feedback history
    feedbacks = db.query(UserDiningFeedback).filter(UserDiningFeedback.user_id == user_id).all()
    cat_net_feedback: dict[str, int] = {}
    disliked_places: set = set()

    for fb in feedbacks:
        if fb.rating == -1:
            disliked_places.add(fb.place_id)
        s = spot_by_id.get(fb.place_id)
        if s:
            cat_net_feedback[s.category] = cat_net_feedback.get(s.category, 0) + fb.rating

    # Base weight calculation: if user has crosswalk signal, use it; otherwise uniform
    max_cw = max(crosswalk_dining.values()) if crosswalk_dining and max(crosswalk_dining.values()) > 0 else 0.0

    category_scores: dict[str, float] = {}
    all_categories = {s.category for s in spots}
    for cat in all_categories:
        if max_cw > 0:
            base_w = crosswalk_dining.get(cat, 0.0)
        else:
            base_w = 1.0

        # Feedback adjustment: +/- 2% per net feedback rating, capped at +/- 10% (0.10)
        net_fb = cat_net_feedback.get(cat, 0)
        adjustment = max(-0.10, min(0.10, net_fb * 0.02))
        category_scores[cat] = base_w * (1.0 + adjustment)

    # Score each spot
    scored_spots = []
    for s in spots:
        score = category_scores.get(s.category, 0.0)
        # If user directly disliked this exact place, downrank it
        if s.place_id in disliked_places:
            score *= 0.5

        # Stable deterministic tie-breaker
        tie_breaker = (abs(hash(s.place_id)) % 10000) / 1e7
        scored_spots.append((score + tie_breaker, s))

    # Sort descending by score
    scored_spots.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored_spots[:limit]]
