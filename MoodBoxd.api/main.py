from fastapi import FastAPI, HTTPException
from scraper import scrape_letterboxd_movies
from enrichment import batch_enrich_movies
import pandas as pd


app = FastAPI(title= "MoodBoxd Scraper API", version="1.0")

@app.get("/")
def root():
    return {"message": "MoodBoxd.api is running!"}

@app.get("/scrape/{username}")
def scrape_user(username: str):
    films = scrape_letterboxd_movies(username)
    if not films:
        raise HTTPException(status_code=404, detail="User not found/ profile is private/ or unable to scrape data.")
    return {
        "username": username,
        "count": len(films),
        "movies": films
    }

@app.get("/scrape-and-enrich/{username}")
async def scrape_and_enrich_user(username: str):
    """Scrape + enrich movies for a user"""
    try:
        # Scrape
        movies = scrape_letterboxd_movies(username)
        
        # Enrich
        enriched = batch_enrich_movies(movies)
        
        # Separate success and errors
        success = [m for m in enriched if 'error' not in m]
        errors = [m for m in enriched if 'error' in m]
        
        return {
            "username": username,
            "total_movies": len(movies),
            "enriched_success": len(success),
            "enriched_errors": len(errors),
            "movies": success,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/export/{username}")
async def export_enriched_csv(username: str):
    """Export enriched data as CSV"""
    try:
        movies = scrape_letterboxd_movies(username)
        enriched = batch_enrich_movies(movies)
        
        df = pd.DataFrame(enriched)
        csv_filename = f"enriched_{username}.csv"
        df.to_csv(csv_filename, index=False)
        
        return {
            "message": "Export successful",
            "filename": csv_filename,
            "row_count": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))