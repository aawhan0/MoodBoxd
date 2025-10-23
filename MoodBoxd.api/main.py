from fastapi import FastAPI

app = FastAPI(title= "MoodBoxd Scraper API", version="1.0")

@app.get("/")
def root():
    return {"message": "MoodBoxd.api is running!"}