"""
tests/test_restaurants.py
Tests for the Restaurant recommendation module.
"""

import pytest
import os
os.environ["GOOGLE_PLACES_API_KEY"] = "test_key"
from fastapi.testclient import TestClient
from unittest.mock import patch
import json

from main import app
from database import get_dynamodb_resource, add_like, remove_like
import services.google_places_client

client = TestClient(app)

# Dummy responses for mock
DUMMY_SEARCH_RESULTS = [
    {
        "place_id": "place_1",
        "name": "Spicy Thai",
        "types": ["restaurant", "food", "thai_restaurant"],
        "rating": 4.5,
        "price_level": 2,
        "address": "123 Main St",
        "photo_reference": "photo1"
    },
    {
        "place_id": "place_2",
        "name": "Thai Basil",
        "types": ["restaurant", "food", "thai_restaurant"],
        "rating": 4.2,
        "price_level": 2,
        "address": "456 Oak St",
        "photo_reference": "photo2"
    },
    {
        "place_id": "place_3",
        "name": "Pizza Palace",
        "types": ["restaurant", "food", "pizza_restaurant"],
        "rating": 4.0,
        "price_level": 1,
        "address": "789 Pine St",
        "photo_reference": "photo3"
    }
]

DUMMY_DETAILS_RESULT = {
    "place_id": "place_1",
    "name": "Spicy Thai",
    "types": ["restaurant", "food", "thai_restaurant"],
    "rating": 4.5,
    "price_level": 2,
    "address": "123 Main St",
    "photo_reference": "photo1",
    "summary": "Great thai food",
    "url": "http://google.com/place_1",
    "location": {"lat": 47.6, "lng": -122.3}
}


@patch("routers.restaurants.search_restaurants")
def test_search_restaurants(mock_search):
    mock_search.return_value = DUMMY_SEARCH_RESULTS
    
    response = client.get("/restaurants/search?q=thai")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 3
    assert data["results"][0]["name"] == "Spicy Thai"


@patch("routers.restaurants.get_restaurant_details")
def test_get_restaurant_details(mock_details):
    mock_details.return_value = DUMMY_DETAILS_RESULT
    
    response = client.get("/restaurants/place_1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Spicy Thai"
    assert data["place_id"] == "place_1"
    
@patch("routers.restaurants.get_restaurant_details")
def test_get_restaurant_not_found(mock_details):
    mock_details.return_value = None
    response = client.get("/restaurants/unknown")
    assert response.status_code == 404


@patch("routers.restaurants.get_restaurant_details")
@patch("routers.restaurants.search_restaurants")
def test_recommend_restaurants(mock_search, mock_details):
    mock_details.return_value = DUMMY_DETAILS_RESULT
    mock_search.return_value = DUMMY_SEARCH_RESULTS
    
    response = client.get("/restaurants/place_1/recommend?n=2")
    assert response.status_code == 200
    data = response.json()
    assert data["place_id"] == "place_1"
    assert data["seed_name"] == "Spicy Thai"
    assert "recommendations" in data
    
    # It should rank Thai Basil higher than Pizza Palace due to thai_restaurant type
    recs = data["recommendations"]
    assert len(recs) == 2
    assert recs[0]["name"] == "Thai Basil"
    assert recs[1]["name"] == "Pizza Palace"
    assert "similarity_score" in recs[0]

# --- Taste Profile Integration ---
@patch("routers.restaurants.get_restaurant_details")
def test_like_unlike_restaurant(mock_details):
    mock_details.return_value = DUMMY_DETAILS_RESULT
    
    # We need a mocked session cookie to pass auth
    from services.auth import serializer
    token = serializer.dumps({"user_id": "test_user"})
    
    # Like
    resp1 = client.post("/restaurants/place_1/like", cookies={"session": token})
    assert resp1.status_code == 201
    assert resp1.json()["liked"] is True
    
    # Unlike
    resp2 = client.delete("/restaurants/place_1/like", cookies={"session": token})
    assert resp2.status_code == 200
    assert resp2.json()["liked"] is False
