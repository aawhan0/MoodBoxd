from fastapi import FastAPI
from app.routes import users

app = FastAPI(title="MoodBoxd API", version="1.0")

app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "MoodBoxd Backend is live!"}