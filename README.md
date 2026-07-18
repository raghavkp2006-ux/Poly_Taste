# Spotify Recommendation Module

This is the Spotify integration module for a FastAPI application. It handles OAuth login, token management (with SQLite storage and auto-refresh), and fetches user listening data (top tracks, top artists, saved tracks).

## Setup Spotify Developer App

To use this module, you need a Spotify Developer application to get your API credentials.

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
2. Log in with your Spotify account.
3. Click on the **Create app** button.
4. Fill in the App name and App description.
5. In the **Redirect URIs** field, enter exactly: `http://127.0.0.1:8000/spotify/callback`.
6. Click **Save** to create the app.
7. Once created, click on the **Settings** button for your app.
8. Here you will find your **Client ID**. Click on **View client secret** to reveal your **Client Secret**.

## Environment Variables

1. Copy `.env.example` to a new file named `.env`:
   ```bash
   cp .env.example .env
   ```
2. Replace `your_client_id_here` and `your_client_secret_here` in `.env` with the values from your Spotify Developer Dashboard.

## How to Test Locally

1. Create a virtual environment and install the dependencies:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   
   pip install -r requirements.txt
   ```

2. Run the FastAPI server:
   ```bash
   python main.py
   ```
   Or use uvicorn directly:
   ```bash
   uvicorn main:app --reload
   ```

3. Open your browser and navigate to:
   [http://127.0.0.1:8000/spotify/login](http://127.0.0.1:8000/spotify/login)

4. Log in with your Spotify account and authorize the app. You will be redirected back to the `/spotify/callback` endpoint which will exchange the authorization code for tokens and save them to the local `spotify_tokens.db` SQLite database.

5. After a successful login, you can test the data fetching endpoints via the browser or the interactive API docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs):
   - [http://127.0.0.1:8000/spotify/top-tracks](http://127.0.0.1:8000/spotify/top-tracks)
   - [http://127.0.0.1:8000/spotify/top-artists](http://127.0.0.1:8000/spotify/top-artists)
   - [http://127.0.0.1:8000/spotify/saved-tracks](http://127.0.0.1:8000/spotify/saved-tracks)
   - [http://127.0.0.1:8000/spotify/recommendations](http://127.0.0.1:8000/spotify/recommendations)

> **Note on Recommendations:** Spotify deprecated their `/recommendations` and `/audio-features` endpoints for new apps in November 2024. Therefore, this module builds a custom content-based recommendation engine. It works by profiling your top artists to generate a weighted genre profile, searching for tracks in your top genres, and scoring those candidates based on genre overlap (excluding tracks you already have in your library or top tracks).

## Integration with the Main App

The router is self-contained in `routers/spotify.py`. You can include it in your main application using:

```python
from routers import spotify
app.include_router(spotify.router)
```

Make sure to initialize the database tables by calling `Base.metadata.create_all(bind=engine)` from `database.py` during your application startup.
