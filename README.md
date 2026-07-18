# Poly_Taste — Multi-Module Recommendation App

A FastAPI application deployed to AWS Lambda via Mangum/SAM, providing content-based recommendations across multiple media domains. Currently supports **Spotify** and **Anime** modules; the Amazon module is planned.

---

## Modules

### Spotify

Genre-profile content-based recommendations. Authenticates users via OAuth and builds a weighted genre fingerprint from their top artists.

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/spotify/login` | Redirects to Spotify OAuth |
| GET | `/spotify/callback` | OAuth callback — stores token |
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

## Setup

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
| `SPOTIFY_CLIENT_ID` | Spotify endpoints | [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) |
| `SPOTIFY_CLIENT_SECRET` | Spotify endpoints | Same app settings page |
| `SPOTIFY_REDIRECT_URI` | Spotify OAuth | Set to `http://127.0.0.1:8000/spotify/callback` |
| `YOUTUBE_API_KEY` | `/anime/{id}/videos` | [console.cloud.google.com](https://console.cloud.google.com/apis/library/youtube.googleapis.com) — enable YouTube Data API v3 |

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

Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive Swagger UI.

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
- **DynamoDB** → Spotify user token storage (production)
- **SQLite** → Spotify user token storage (local dev, auto-detected)
- **S3** → Anime/Amazon static catalog storage (production)
- **Local JSON** → Catalog fallback (local dev, auto-detected)
