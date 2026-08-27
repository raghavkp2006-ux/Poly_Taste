"""
database.py — Dual-backend user-token storage.

Backend selection
-----------------
Set the environment variable  USE_LOCAL_DB=true  (or simply omit AWS
credentials) to use a local SQLite database via SQLAlchemy.  This mirrors
the pattern already used in services/jikan_client.py for the anime catalog.

When running on AWS Lambda, leave USE_LOCAL_DB unset (or set it to any
value other than "true") and ensure standard AWS credential env-vars /
instance-profile are configured.  The DynamoDB path is identical to the
original implementation.

Exports
-------
Always available:
  get_user(user_id)                         → Optional[Dict]
  get_user_by_id(user_id)                   → Optional[Dict]
  get_user_by_google_sub(google_sub)        → Optional[Dict]
  upsert_user(user_id, access_token,
              refresh_token, expires_at)    → None
  upsert_google_user(google_sub, email,
                     name, picture_url)    → Dict
  delete_user(user_id)                      → None

  add_like(user_id, module, item_id)        → None
  remove_like(user_id, module, item_id)     → None
  get_likes(user_id, module=None)           → List[Dict]

Local-dev mode only (None in Lambda/DynamoDB mode):
  SessionLocal    — SQLAlchemy session factory
  SpotifyUser     — SQLAlchemy ORM model
  User            — SQLAlchemy ORM model (Google identity)
  UserLike        — SQLAlchemy ORM model
  Base            — declarative_base (for create_all)
"""

import os
import time
from typing import Optional, Dict, Any, List

# ---------------------------------------------------------------------------
# Detect which backend to use
# ---------------------------------------------------------------------------
_use_local = os.getenv("USE_LOCAL_DB", "").lower() == "true"

# Also fall back to local when no AWS region / key is configured, so that
# bare `python main.py` without any AWS setup doesn't crash on import.
if not _use_local:
    _has_aws = bool(
        os.getenv("AWS_DEFAULT_REGION")
        or os.getenv("AWS_ACCESS_KEY_ID")
        or os.getenv("AWS_PROFILE")
    )
    if not _has_aws:
        _use_local = True
        print(
            "[database] No AWS credentials detected — switching to local SQLite mode. "
            "Set USE_LOCAL_DB=false to suppress this and use DynamoDB."
        )

# ---------------------------------------------------------------------------
# LOCAL mode — SQLite via SQLAlchemy
# ---------------------------------------------------------------------------
if _use_local:
    from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, UniqueConstraint, ForeignKey, text, func
    from sqlalchemy.orm import declarative_base, sessionmaker, relationship
    from datetime import datetime, timezone

    _db_url = os.getenv("DATABASE_URL")
    if _db_url:
        _engine = create_engine(_db_url)
    else:
        _DB_PATH = os.getenv(
            "SQLITE_PATH",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "spotify_tokens.db"),
        )
        _engine = create_engine(f"sqlite:///{_DB_PATH}", connect_args={"check_same_thread": False})
    engine = _engine
    Base = declarative_base()

    class SpotifyUser(Base):  # type: ignore[valid-type]
        """ORM model for local-dev SQLite user-token storage."""

        __tablename__ = "spotify_users"

        user_id = Column(String, primary_key=True, index=True)
        access_token = Column(String, nullable=False)
        refresh_token = Column(String, nullable=True)
        expires_at = Column(Integer, nullable=False)
        spotify_account_id = Column(String, nullable=True)
        spotify_display_name = Column(String, nullable=True)

        def to_dict(self) -> Dict[str, Any]:
            return {
                "user_id": self.user_id,
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.expires_at,
                "spotify_account_id": self.spotify_account_id,
                "spotify_display_name": self.spotify_display_name,
            }

    class User(Base):  # type: ignore[valid-type]
        """ORM model for Google-identity users."""

        __tablename__ = "users"

        id = Column(Integer, primary_key=True, autoincrement=True)
        google_sub = Column(String, unique=True, nullable=False, index=True)
        email = Column(String, nullable=False)
        name = Column(String, nullable=True)
        picture_url = Column(String, nullable=True)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

        def to_dict(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "google_sub": self.google_sub,
                "email": self.email,
                "name": self.name,
                "picture_url": self.picture_url,
                "created_at": self.created_at.isoformat() if self.created_at else None,
            }

    class UserLike(Base):  # type: ignore[valid-type]
        """ORM model for per-user cross-module likes (anime, amazon)."""

        __tablename__ = "user_likes"
        __table_args__ = (
            UniqueConstraint("user_id", "module", "item_id", name="uq_user_module_item"),
        )

        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(String, nullable=False, index=True)
        module = Column(String, nullable=False)   # "anime" | "amazon"
        item_id = Column(String, nullable=False)  # mal_id or product_id as str
        liked_at = Column(Integer, nullable=False)  # Unix epoch seconds

        def to_dict(self) -> Dict[str, Any]:
            return {
                "user_id": self.user_id,
                "module": self.module,
                "item_id": self.item_id,
                "liked_at": self.liked_at,
            }


    class AniListUser(Base):  # type: ignore[valid-type]
        """ORM model for local-dev SQLite AniList user-token storage."""

        __tablename__ = "anilist_users"

        user_id = Column(String, ForeignKey("users.id"), primary_key=True, index=True)
        anilist_id = Column(Integer, nullable=False)
        anilist_username = Column(String, nullable=False)
        access_token = Column(String, nullable=False)
        connected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

        def to_dict(self) -> Dict[str, Any]:
            return {
                "user_id": self.user_id,
                "anilist_id": self.anilist_id,
                "anilist_username": self.anilist_username,
                "access_token": self.access_token,
                "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            }

    class SpotifyImportProfile(Base):  # type: ignore[valid-type]
        """ORM model for imported Spotify streaming history genre profiles."""

        __tablename__ = "spotify_import_profiles"

        user_id = Column(String, primary_key=True, index=True)
        genre_profile_json = Column(String, nullable=False)   # JSON {genre: weight}
        artist_summary_json = Column(String, nullable=True)   # JSON top-50 artists
        total_plays = Column(Integer, nullable=True)
        unique_artists = Column(Integer, nullable=True)
        imported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

        def to_dict(self) -> Dict[str, Any]:
            return {
                "user_id": self.user_id,
                "genre_profile_json": self.genre_profile_json,
                "artist_summary_json": self.artist_summary_json,
                "total_plays": self.total_plays,
                "unique_artists": self.unique_artists,
                "imported_at": self.imported_at.isoformat() if self.imported_at else None,
            }

    class TouristSpot(Base):
        __tablename__ = "tourist_spots"

        place_id = Column(String, primary_key=True)
        name = Column(String, nullable=False)
        category = Column(String, nullable=False, index=True)
        description = Column(String, nullable=True)
        price_tier = Column(String, nullable=False)
        lat = Column(Float, nullable=False)
        lng = Column(Float, nullable=False)
        city = Column(String, nullable=False, default="Chennai")

    class UserSpotFeedback(Base):
        __tablename__ = "user_spot_feedback"

        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(String, ForeignKey("users.google_sub"), nullable=False, index=True)
        place_id = Column(String, ForeignKey("tourist_spots.place_id"), nullable=False, index=True)
        rating = Column(Integer, nullable=False)
        tag = Column(String, nullable=True)
        created_at = Column(DateTime, nullable=False, server_default=func.now())

    TOURIST_SPOT_CATEGORIES = [
        "adventure_outdoor",
        "cultural_historic",
        "nightlife",
        "chill_scenic",
        "shopping_social",
        "offbeat_indie",
    ]

    class DiningSpot(Base):
        """ORM model for restaurants/cafes catalog entries.

        Sourced from OpenStreetMap Overpass export — this is bootstrap data,
        NOT curated hand-written entries.  Descriptions and price tiers are
        not available in the OSM data and default to NULL.
        """
        __tablename__ = "dining_spots"

        place_id = Column(String, primary_key=True)
        name = Column(String, nullable=False)
        category = Column(String, nullable=False, index=True)
        description = Column(String, nullable=True)   # NULL — not in OSM data
        price_tier = Column(String, nullable=True)     # NULL — not in OSM data
        cuisine = Column(String, nullable=True)        # Raw OSM cuisine tag
        lat = Column(Float, nullable=False)
        lng = Column(Float, nullable=False)
        city = Column(String, nullable=False, default="Chennai")
        osm_id = Column(String, nullable=True)         # e.g. "node/12345"

    class UserDiningFeedback(Base):
        """User like/dislike feedback on dining spots — mirrors UserSpotFeedback."""
        __tablename__ = "user_dining_feedback"

        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(String, ForeignKey("users.google_sub"), nullable=False, index=True)
        place_id = Column(String, ForeignKey("dining_spots.place_id"), nullable=False, index=True)
        rating = Column(Integer, nullable=False)
        tag = Column(String, nullable=True)
        created_at = Column(DateTime, nullable=False, server_default=func.now())

    DINING_CATEGORIES = [
        "fine_dining",
        "casual_dining",
        "street_food_quick_bite",
        "cafe_coffee",
        "dessert_bakery",
        "bar_nightlife_dining",
    ]

    class Movie(Base):  # type: ignore[valid-type]
        """ORM model for TMDB movie catalog entries.

        Each row represents a movie fetched from the TMDB API.
        The ``personal_rating`` field stores Raghav's own IMDb rating
        (1–10 float, nullable) imported from an IMDb CSV export.
        """

        __tablename__ = "movies"

        id = Column(Integer, primary_key=True, autoincrement=True)
        tmdb_id = Column(Integer, unique=True, nullable=False, index=True)
        imdb_id = Column(String, unique=True, nullable=True, index=True)  # "tt..." string
        title = Column(String, nullable=False)
        overview = Column(String, nullable=True)
        genres_json = Column(String, nullable=True)       # JSON list of genre strings, e.g. '["Action","Drama"]'
        release_year = Column(Integer, nullable=True)
        poster_url = Column(String, nullable=True)         # Full TMDB poster URL
        vote_average = Column(Float, nullable=True)       # TMDB average vote (0–10 scale)
        personal_rating = Column(Float, nullable=True)     # Raghav's IMDb rating (1–10 scale)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

        def to_dict(self) -> Dict[str, Any]:
            import json as _json
            return {
                "id": self.id,
                "tmdb_id": self.tmdb_id,
                "imdb_id": self.imdb_id,
                "title": self.title,
                "overview": self.overview,
                "genres": _json.loads(self.genres_json) if self.genres_json else [],
                "release_year": self.release_year,
                "poster_url": self.poster_url,
                "vote_average": self.vote_average,
                "personal_rating": self.personal_rating,
                "created_at": self.created_at.isoformat() if self.created_at else None,
            }

    try:
        Base.metadata.create_all(bind=_engine)

        # Inline schema migration to add new columns to existing DB if missing
        if _engine.dialect.name == "sqlite":
            with _engine.begin() as conn:
                result = conn.execute(text("PRAGMA table_info(spotify_users)"))
                columns = [row[1] for row in result]
                if "spotify_account_id" not in columns:
                    conn.execute(text("ALTER TABLE spotify_users ADD COLUMN spotify_account_id TEXT"))
                if "spotify_display_name" not in columns:
                    conn.execute(text("ALTER TABLE spotify_users ADD COLUMN spotify_display_name TEXT"))

                # Migration for movies table
                m_result = conn.execute(text("PRAGMA table_info(movies)"))
                m_columns = [row[1] for row in m_result]
                if "vote_average" not in m_columns:
                    conn.execute(text("ALTER TABLE movies ADD COLUMN vote_average REAL"))

                conn.execute(text("DROP TABLE IF EXISTS restaurants"))
                conn.execute(text("DROP TABLE IF EXISTS restaurant_reviews"))
    except Exception:
        pass

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # ----- public API (local) -----

    def get_user(user_id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            user = db.query(SpotifyUser).filter(SpotifyUser.user_id == user_id).first()
            return user.to_dict() if user else None
        finally:
            db.close()

    def get_anilist_user(user_id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            user = db.query(AniListUser).filter(AniListUser.user_id == user_id).first()
            return user.to_dict() if user else None
        finally:
            db.close()

    def upsert_anilist_user(
        user_id: str,
        anilist_id: int,
        anilist_username: str,
        access_token: str,
    ) -> None:
        db = SessionLocal()
        try:
            user = db.query(AniListUser).filter(AniListUser.user_id == user_id).first()
            if user:
                user.anilist_id = anilist_id
                user.anilist_username = anilist_username
                user.access_token = access_token
            else:
                user = AniListUser(
                    user_id=user_id,
                    anilist_id=anilist_id,
                    anilist_username=anilist_username,
                    access_token=access_token,
                )
                db.add(user)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[database] upsert_anilist_user({user_id}): {e}")
        finally:
            db.close()

    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Look up either a Spotify or Google user by internal user_id."""
        db = SessionLocal()
        try:
            user = db.query(SpotifyUser).filter(SpotifyUser.user_id == user_id).first()
            if user:
                return user.to_dict()
            user = db.query(User).filter(User.id == int(user_id)).first()
            return user.to_dict() if user else None
        except (ValueError, TypeError):
            return None
        finally:
            db.close()

    def get_user_by_google_sub(google_sub: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.google_sub == google_sub).first()
            return user.to_dict() if user else None
        finally:
            db.close()

    def upsert_google_user(
        google_sub: str,
        email: str,
        name: Optional[str],
        picture_url: Optional[str],
    ) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.google_sub == google_sub).first()
            if user:
                user.email = email
                user.name = name
                user.picture_url = picture_url
            else:
                user = User(
                    google_sub=google_sub,
                    email=email,
                    name=name,
                    picture_url=picture_url,
                )
                db.add(user)
            db.commit()
            db.refresh(user)
            return user.to_dict()
        except Exception as e:
            db.rollback()
            print(f"[database] upsert_google_user({google_sub}): {e}")
            raise
        finally:
            db.close()

    def upsert_user(
        user_id: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: int,
        spotify_account_id: Optional[str] = None,
        spotify_display_name: Optional[str] = None,
    ) -> None:
        db = SessionLocal()
        try:
            user = db.query(SpotifyUser).filter(SpotifyUser.user_id == user_id).first()
            if user:
                user.access_token = access_token
                if refresh_token:
                    user.refresh_token = refresh_token
                user.expires_at = expires_at
                if spotify_account_id:
                    user.spotify_account_id = spotify_account_id
                if spotify_display_name:
                    user.spotify_display_name = spotify_display_name
            else:
                user = SpotifyUser(
                    user_id=user_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
                    spotify_account_id=spotify_account_id,
                    spotify_display_name=spotify_display_name,
                )
                db.add(user)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[database] upsert_user({user_id}): {e}")
        finally:
            db.close()

    def delete_user(user_id: str) -> None:
        db = SessionLocal()
        try:
            user = db.query(SpotifyUser).filter(SpotifyUser.user_id == user_id).first()
            if user:
                db.delete(user)
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"[database] delete_user({user_id}): {e}")
        finally:
            db.close()

    def get_dynamodb_resource():  # noqa: D103
        raise RuntimeError(
            "get_dynamodb_resource() called in local-dev mode. "
            "Unset USE_LOCAL_DB or configure AWS credentials to use DynamoDB."
        )

    def add_like(user_id: str, module: str, item_id: str) -> None:
        """Record that user liked item_id in the given module. Idempotent."""
        db = SessionLocal()
        try:
            existing = (
                db.query(UserLike)
                .filter(
                    UserLike.user_id == user_id,
                    UserLike.module == module,
                    UserLike.item_id == item_id,
                )
                .first()
            )
            if not existing:
                like = UserLike(
                    user_id=user_id,
                    module=module,
                    item_id=item_id,
                    liked_at=int(time.time()),
                )
                db.add(like)
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"[database] add_like({user_id}, {module}, {item_id}): {e}")
        finally:
            db.close()

    def remove_like(user_id: str, module: str, item_id: str) -> None:
        """Remove a like. No-op if the like doesn't exist."""
        db = SessionLocal()
        try:
            like = (
                db.query(UserLike)
                .filter(
                    UserLike.user_id == user_id,
                    UserLike.module == module,
                    UserLike.item_id == item_id,
                )
                .first()
            )
            if like:
                db.delete(like)
                db.commit()
        except Exception as e:
            db.rollback()
            print(f"[database] remove_like({user_id}, {module}, {item_id}): {e}")
        finally:
            db.close()

    def get_likes(user_id: str, module: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all likes for a user, optionally filtered by module."""
        db = SessionLocal()
        try:
            q = db.query(UserLike).filter(UserLike.user_id == user_id)
            if module:
                q = q.filter(UserLike.module == module)
            return [row.to_dict() for row in q.order_by(UserLike.liked_at.desc()).all()]
        finally:
            db.close()

    def upsert_spotify_import_profile(
        user_id: str,
        genre_profile_json: str,
        artist_summary_json: Optional[str] = None,
        total_plays: Optional[int] = None,
        unique_artists: Optional[int] = None,
    ) -> None:
        """Store or update an imported Spotify streaming history genre profile."""
        db = SessionLocal()
        try:
            row = db.query(SpotifyImportProfile).filter(
                SpotifyImportProfile.user_id == user_id
            ).first()
            if row:
                row.genre_profile_json = genre_profile_json
                row.artist_summary_json = artist_summary_json
                row.total_plays = total_plays
                row.unique_artists = unique_artists
                row.imported_at = datetime.now(timezone.utc)
            else:
                row = SpotifyImportProfile(
                    user_id=user_id,
                    genre_profile_json=genre_profile_json,
                    artist_summary_json=artist_summary_json,
                    total_plays=total_plays,
                    unique_artists=unique_artists,
                )
                db.add(row)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[database] upsert_spotify_import_profile({user_id}): {e}")
        finally:
            db.close()

    def get_spotify_import_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the imported Spotify genre profile for a user, if any."""
        db = SessionLocal()
        try:
            row = db.query(SpotifyImportProfile).filter(
                SpotifyImportProfile.user_id == user_id
            ).first()
            return row.to_dict() if row else None
        finally:
            db.close()

# ---------------------------------------------------------------------------
# AWS / Lambda mode — DynamoDB (unchanged from original)
# ---------------------------------------------------------------------------
else:
    import boto3
    from botocore.exceptions import ClientError

    # Stubs so that imports don't break in Lambda
    SessionLocal = None  # type: ignore[assignment]
    SpotifyUser = None   # type: ignore[assignment]
    User = None          # type: ignore[assignment]
    UserLike = None      # type: ignore[assignment]
    AniListUser = None   # type: ignore[assignment]
    SpotifyImportProfile = None  # type: ignore[assignment]
    TouristSpot = None   # type: ignore[assignment]
    UserSpotFeedback = None  # type: ignore[assignment]
    Base = None          # type: ignore[assignment]
    get_db = None        # type: ignore[assignment]

    TOURIST_SPOT_CATEGORIES = [
        "adventure_outdoor",
        "cultural_historic",
        "nightlife",
        "chill_scenic",
        "shopping_social",
        "offbeat_indie",
    ]

    DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "spotify_users")
    USER_LIKES_TABLE_NAME = os.getenv("USER_LIKES_TABLE_NAME", "user_likes")
    USERS_TABLE_NAME = os.getenv("USERS_TABLE_NAME", "users")
    ANILIST_USERS_TABLE_NAME = os.getenv("ANILIST_USERS_TABLE_NAME", "anilist_users")

    def get_dynamodb_resource():  # noqa: D103
        return boto3.resource("dynamodb")

    def get_user(user_id: str) -> Optional[Dict[str, Any]]:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        try:
            response = table.get_item(Key={"user_id": user_id})
            return response.get("Item")
        except ClientError as e:
            print(f"[database] get_user({user_id}): {e}")
            return None

    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        return get_user(user_id)

    def get_user_by_google_sub(google_sub: str) -> Optional[Dict[str, Any]]:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(USERS_TABLE_NAME)
        try:
            response = table.get_item(Key={"google_sub": google_sub})
            return response.get("Item")
        except ClientError as e:
            print(f"[database] get_user_by_google_sub({google_sub}): {e}")
            return None

    def upsert_google_user(
        google_sub: str,
        email: str,
        name: Optional[str],
        picture_url: Optional[str],
    ) -> Dict[str, Any]:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(USERS_TABLE_NAME)
        item: Dict[str, Any] = {
            "google_sub": google_sub,
            "email": email,
            "name": name or "",
            "picture_url": picture_url or "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            table.put_item(Item=item)
            return item
        except ClientError as e:
            print(f"[database] upsert_google_user({google_sub}): {e}")
            raise

    def upsert_user(
        user_id: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: int,
        spotify_account_id: Optional[str] = None,
        spotify_display_name: Optional[str] = None,
    ) -> None:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        item: Dict[str, Any] = {
            "user_id": user_id,
            "access_token": access_token,
            "expires_at": expires_at,
        }
        if refresh_token:
            item["refresh_token"] = refresh_token
        if spotify_account_id:
            item["spotify_account_id"] = spotify_account_id
        if spotify_display_name:
            item["spotify_display_name"] = spotify_display_name
        try:
            table.put_item(Item=item)
        except ClientError as e:
            print(f"[database] upsert_user({user_id}): {e}")

    def delete_user(user_id: str) -> None:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(DYNAMODB_TABLE_NAME)
        try:
            table.delete_item(Key={"user_id": user_id})
        except ClientError as e:
            print(f"[database] delete_user({user_id}): {e}")

    def add_like(user_id: str, module: str, item_id: str) -> None:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(USER_LIKES_TABLE_NAME)
        try:
            table.put_item(Item={
                "pk": f"{user_id}#{module}#{item_id}",
                "user_id": user_id,
                "module": module,
                "item_id": item_id,
                "liked_at": int(time.time()),
            })
        except ClientError as e:
            print(f"[database] add_like({user_id}, {module}, {item_id}): {e}")

    def remove_like(user_id: str, module: str, item_id: str) -> None:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(USER_LIKES_TABLE_NAME)
        try:
            table.delete_item(Key={"pk": f"{user_id}#{module}#{item_id}"})
        except ClientError as e:
            print(f"[database] remove_like({user_id}, {module}, {item_id}): {e}")

    def get_likes(user_id: str, module: Optional[str] = None) -> List[Dict[str, Any]]:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(USER_LIKES_TABLE_NAME)
        try:
            filter_expr = "user_id = :uid"
            expr_vals: Dict[str, Any] = {":uid": user_id}
            if module:
                filter_expr += " AND #mod = :mod"
                expr_vals[":mod"] = module
            kwargs = {
                "FilterExpression": filter_expr,
                "ExpressionAttributeValues": expr_vals,
            }
            if module:
                kwargs["ExpressionAttributeNames"] = {"#mod": "module"}
            resp = table.scan(**kwargs)
            return resp.get("Items", [])
        except ClientError as e:
            print(f"[database] get_likes({user_id}): {e}")
            return []

    def get_anilist_user(user_id: str) -> Optional[Dict[str, Any]]:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(ANILIST_USERS_TABLE_NAME)
        try:
            response = table.get_item(Key={"user_id": user_id})
            return response.get("Item")
        except ClientError as e:
            print(f"[database] get_anilist_user({user_id}): {e}")
            return None

    def upsert_anilist_user(
        user_id: str,
        anilist_id: int,
        anilist_username: str,
        access_token: str,
    ) -> None:
        dynamodb = get_dynamodb_resource()
        table = dynamodb.Table(ANILIST_USERS_TABLE_NAME)
        item: Dict[str, Any] = {
            "user_id": user_id,
            "anilist_id": anilist_id,
            "anilist_username": anilist_username,
            "access_token": access_token,
            "connected_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            table.put_item(Item=item)
        except ClientError as e:
            print(f"[database] upsert_anilist_user({user_id}): {e}")

    def upsert_spotify_import_profile(
        user_id: str,
        genre_profile_json: str,
        artist_summary_json: Optional[str] = None,
        total_plays: Optional[int] = None,
        unique_artists: Optional[int] = None,
    ) -> None:
        """Store imported Spotify profile — DynamoDB stub (not yet implemented)."""
        print(f"[database] upsert_spotify_import_profile: DynamoDB not implemented")

    def get_spotify_import_profile(user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve imported Spotify profile — DynamoDB stub (not yet implemented)."""
        print(f"[database] get_spotify_import_profile: DynamoDB not implemented")
        return None
