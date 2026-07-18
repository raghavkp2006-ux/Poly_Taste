from fastapi import FastAPI
import uvicorn
from database import get_dynamodb_resource
from routers import spotify, anime

app = FastAPI(title="Multi-Module Recommendation App")

app.include_router(spotify.router)
app.include_router(anime.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Recommendation App API! Visit /docs for Swagger UI"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
