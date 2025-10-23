from fastapi import FastAPI

app = FastAPI(title="MoodBoxd API", version="1.0")

@app.get("/")
def root():
    return {"message": "MoodBoxd backend is live!"}