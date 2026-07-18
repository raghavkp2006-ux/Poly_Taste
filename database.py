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
  upsert_user(user_id, access_token,
              refresh_token, expires_at)    → None
  delete_user(user_id)                      → None

Local-dev mode only (None in Lambda/DynamoDB mode):
  SessionLocal    — SQLAlchemy session factory
  SpotifyUser     — SQLAlchemy ORM model
  Base            — declarative_base (for create_all)
"""

import os
from typing import Optional, Dict, Any

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
    from sqlalchemy import create_engine, Column, String, Integer
    from sqlalchemy.orm import declarative_base, sessionmaker

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

    Base.metadata.create_all(bind=_engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    # ----- public API (local) -----

    def get_user(user_id: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            user = db.query(SpotifyUser).filter(SpotifyUser.user_id == user_id).first()
            return user.to_dict() if user else None
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

# ---------------------------------------------------------------------------
# AWS / Lambda mode — DynamoDB (unchanged from original)
# ---------------------------------------------------------------------------
else:
    import boto3
    from botocore.exceptions import ClientError

    # Stubs so that imports don't break in Lambda
    SessionLocal = None  # type: ignore[assignment]
    SpotifyUser = None   # type: ignore[assignment]
    Base = None          # type: ignore[assignment]

    DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "spotify_users")

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
