from fastapi import FastAPI, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from database import get_dynamodb_resource
from routers import google_auth, spotify, spotify_import, anime, taste, anilist, connections, tourist_spots, movie, dining
from services.auth import get_current_user_id, create_session_cookie
from pydantic import BaseModel
from fastapi import HTTPException

app = FastAPI(title="Multi-Module Recommendation App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(google_auth.router)
app.include_router(spotify.router)
app.include_router(spotify_import.router)
app.include_router(anime.router)
app.include_router(movie.router)
app.include_router(taste.router)
app.include_router(anilist.router)
app.include_router(connections.router)
app.include_router(tourist_spots.router)
app.include_router(dining.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Recommendation App API! Visit /docs for Swagger UI"}

@app.get("/auth/me")
def get_me(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id}

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/login")
def login(req: LoginRequest, response: Response):
    if req.email and req.password:
        session_cookie = create_session_cookie(user_id=req.email)
        response.set_cookie(
            key="session",
            value=session_cookie,
            httponly=True,
            samesite="lax",
            max_age=30 * 24 * 60 * 60
        )
        return {"message": "Login successful", "user_id": req.email}
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password. Please try again.")

@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(key="session", httponly=True, samesite="lax")
    return {"message": "Logged out successfully"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
