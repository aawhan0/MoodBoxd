from fastapi import FastAPI, HTTPException
from scraper import scrape_letterboxd_movies

app = FastAPI(title= "MoodBoxd Scraper API", version="1.0")

@app.get("/")
def root():
    return {"message": "MoodBoxd.api is running!"}

@app.get("/scrape/{username}")
def scrape_user(username: str):
    films = scrape_letterboxd_movies(username)
    if films is None:
        raise HTTPException(status_code=404, detail="User not found or unable to scrape data.")
    return {"username": username, "movies": films}