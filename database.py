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
  Restaurant      — SQLAlchemy ORM model
  Review          — SQLAlchemy ORM model
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
    from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, UniqueConstraint, ForeignKey
    from sqlalchemy.orm import declarative_base, sessionmaker, relationship
    from datetime import datetime, timezone

    _DB_PATH = os.getenv(
        "SQLITE_PATH",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "spotify_tokens.db"),
    )
    _engine = create_engine(f"sqlite:///{_DB_PATH}", connect_args={"check_same_thread": False})
    Base = declarative_base()

    class SpotifyUser(Base):  # type: ignore[valid-type]
        """ORM model for local-dev SQLite user-token storage."""

        __tablename__ = "spotify_users"

        user_id = Column(String, primary_key=True, index=True)
        access_token = Column(String, nullable=False)
        refresh_token = Column(String, nullable=True)
        expires_at = Column(Integer, nullable=False)

        def to_dict(self) -> Dict[str, Any]:
            return {
                "user_id": self.user_id,
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.expires_at,
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

    class Restaurant(Base):  # type: ignore[valid-type]
        __tablename__ = "restaurants"
        id = Column(Integer, primary_key=True, autoincrement=True)
        place_id = Column(String, unique=True, nullable=False, index=True)
        name = Column(String, nullable=False)
        vicinity = Column(String, nullable=True)
        rating = Column(Float, nullable=True)
        types = Column(String, nullable=True)

    class Review(Base):  # type: ignore[valid-type]
        __tablename__ = "restaurant_reviews"
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(String, nullable=False, index=True)
        place_id = Column(String, nullable=False, index=True)
        place_name = Column(String, nullable=False)
        place_types = Column(String, nullable=True) # comma separated
        rating = Column(Integer, nullable=False)
        comment = Column(String, nullable=True)
        created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

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

    Base.metadata.create_all(bind=_engine)
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
    ) -> None:
        db = SessionLocal()
        try:
            user = db.query(SpotifyUser).filter(SpotifyUser.user_id == user_id).first()
            if user:
                user.access_token = access_token
                if refresh_token:
                    user.refresh_token = refresh_token
                user.expires_at = expires_at
            else:
                user = SpotifyUser(
                    user_id=user_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    expires_at=expires_at,
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
    Restaurant = None    # type: ignore[assignment]
    Review = None        # type: ignore[assignment]
    AniListUser = None   # type: ignore[assignment]
    Base = None          # type: ignore[assignment]
    get_db = None        # type: ignore[assignment]

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
