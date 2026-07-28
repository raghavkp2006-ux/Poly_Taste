import os
from fastapi import Request, HTTPException, status
from itsdangerous import URLSafeSerializer
from dotenv import load_dotenv

load_dotenv()

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "dev_secret_key_change_me_in_prod")

serializer = URLSafeSerializer(SESSION_SECRET_KEY, salt="session-cookie")

def create_session_cookie(user_id: str) -> str:
    """Sign the user_id into a session cookie string."""
    return serializer.dumps({"user_id": user_id})

def get_current_user_id(request: Request) -> str:
    """
    FastAPI dependency to get the current user_id from the session cookie.
    Raises 401 Unauthorized if missing or invalid.
    """
    cookie = request.cookies.get("session")
    if not cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
        )
    try:
        data = serializer.loads(cookie)
        user_id = data.get("user_id")
        if not user_id:
            raise ValueError("No user_id in session")
        return user_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
        )
