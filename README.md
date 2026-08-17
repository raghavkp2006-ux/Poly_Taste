# Poly_Taste — Multi-Module Recommendation App

A FastAPI application deployed to AWS Lambda via Mangum/SAM, providing content-based recommendations across multiple media domains. Currently supports **Spotify**, **Anime**, and **Restaurants** modules.

---

## Modules

### Auth / Session

The app uses a signed cookie session for authentication, established via Google Sign-In (keyed on `google_sub`). Spotify and AniList are optional secondary connections linked to this primary Google session to pull listening/watch data into the taste profile. They do not create or overwrite the session on their own.

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/google/login` | Sign in with Google (starts the app-wide login flow) |
| GET | `/auth/google/callback` | OAuth callback — verifies identity, sets session cookie |
| GET | `/auth/me` | Returns current `user_id` if logged in (401 otherwise) |
| POST | `/auth/logout` | Clears the session cookie |

---

### Spotify

Genre-profile content-based recommendations. Users can optionally connect their Spotify account to their Google session via OAuth to build a weighted genre fingerprint from their top artists.

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/spotify/login` | Connect Spotify account (links to existing Google session) |
| GET | `/spotify/callback` | OAuth callback — stores Spotify token for the current user |
| GET | `/spotify/top-tracks` | User's top 10 tracks |
| GET | `/spotify/recommendations` | Genre-profile track recommendations |
| GET | `/spotify/recommend/{track_id}` | **[Deprecated]** DNN similarity via `/audio-features` (unavailable for new apps since Nov 2024) |

---

### Anime

TF-IDF + AutoEncoder similarity over a Kitsu-sourced catalog, plus live data from AniList, YouTube, and Anime News Network.

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/anime/search?q=` | Substring title search on catalog |
| GET | `/anime/upcoming` | Upcoming anime (AniList GraphQL, Jikan fallback) |
| GET | `/anime/{mal_id}` | Single catalog entry |
| GET | `/anime/{mal_id}/recommend` | TF-IDF/AutoEncoder similarity recommendations |
| GET | `/anime/{mal_id}/reviews` | Review snippets (AniList, Jikan fallback) |
| GET | `/anime/{mal_id}/videos` | YouTube trailers/explainers — requires `YOUTUBE_API_KEY` |
| GET | `/anime/{mal_id}/news` | Anime News Network RSS articles filtered by title |

#### Data Sources

- **Catalog**: Kitsu API (`services/jikan_client.py`) — run once locally or on a schedule to populate `data/raw/anime_catalog.json`
- **Upcoming / Reviews**: AniList public GraphQL API (`services/anilist_client.py`) — no API key required
- **Videos**: YouTube Data API v3 — requires `YOUTUBE_API_KEY` (see setup below)
- **News**: Anime News Network RSS feed — no API key required

---

### Restaurants

Content similarity recommendations using the Google Places API. It searches for nearby restaurants based on a seed restaurant's types/cuisines and price level, using TF-IDF and cosine similarity to rank candidates.

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/restaurants/search?q=&location=` | Text search via Google Places API |
| GET | `/restaurants/{place_id}` | Full details for a single restaurant |
| GET | `/restaurants/{place_id}/recommend` | TF-IDF/cosine similarity recommendations based on cuisine and price |

#### Setup

1. Obtain a Google Places API Key from the Google Cloud Console.
2. Enable the **Places API (New)** or standard **Places API**.
3. Set the `GOOGLE_PLACES_API_KEY` in your `.env` file.

### 1. Clone and install

```bash
git clone https://github.com/raghavkp2006-ux/Poly_Taste.git
cd Poly_Taste
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Required for | Where to get it |
|----------|-------------|-----------------|
| `GOOGLE_CLIENT_ID` | Google Sign-In | [console.cloud.google.com](https://console.cloud.google.com/) |
| `GOOGLE_CLIENT_SECRET` | Google Sign-In | Same app settings page |
| `GOOGLE_REDIRECT_URI` | Google Sign-In | Set to `http://127.0.0.1:8000/auth/google/callback` exactly. |
| `SPOTIFY_CLIENT_ID` | Spotify endpoints | [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) |
| `SPOTIFY_CLIENT_SECRET` | Spotify endpoints | Same app settings page |
| `SPOTIFY_REDIRECT_URI` | Spotify OAuth | Set to `http://127.0.0.1:8000/spotify/callback` exactly. **Note:** Access the app via http://127.0.0.1:8000, not localhost. |
| `SESSION_SECRET_KEY` | App authentication | Set to a random secure string in production |
| `YOUTUBE_API_KEY` | `/anime/{id}/videos` | [console.cloud.google.com](https://console.cloud.google.com/apis/library/youtube.googleapis.com) — enable YouTube Data API v3 |
| `GOOGLE_PLACES_API_KEY` | `/restaurants/*` | [console.cloud.google.com](https://console.cloud.google.com/apis/library/places-backend.googleapis.com) — enable Places API |

> **YouTube quota note:** `search.list` costs 100 quota units per call. The free tier provides 10,000 units/day, supporting ~100 video searches/day.

AWS variables (`DYNAMODB_TABLE_NAME`, `S3_BUCKET_NAME`, `AWS_DEFAULT_REGION`) are only needed for production Lambda deployment. The app automatically uses SQLite + local JSON files when these are absent.

### 3. Populate the anime catalog (one-time)

```bash
python services/jikan_client.py
```

This fetches 100 top-rated anime from Kitsu (including genres) and saves them to `data/raw/anime_catalog.json`.

### 4. Run locally

```bash
python main.py
# or
uvicorn main:app --reload
```

To test the application flow:
1. Start the app and visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive Swagger UI, or launch the frontend.
2. Sign in with Google first (via `/auth/google/login`).
3. Once a session is established, you can optionally connect Spotify or AniList to pull in your taste data.

---

## Running Tests

```bash
pytest tests/ -v
```

All external HTTP calls are mocked in the test suite — no live API access or credentials are required to run tests.

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full AWS infrastructure diagram.

- **FastAPI** + **Mangum** → single AWS Lambda function
- **DynamoDB** → User identity & OAuth token storage (production)
- **SQLite** → User identity & OAuth token storage (local dev, auto-detected)
- **S3** → Anime/Amazon static catalog storage (production)
- **Local JSON** → Catalog fallback (local dev, auto-detected)


