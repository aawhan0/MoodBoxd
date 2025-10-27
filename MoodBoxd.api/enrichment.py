from imdb import IMDb
import requests
from bs4 import BeautifulSoup
import re
import time


ia = IMDb()


# List of IMDb kinds to exclude (not movies)
EXCLUDED_KINDS = {"podcast", "tv episode", "video", "video game", "tv series", "tv mini series"}


def clean_movie_title(raw_title):
    """Remove 'Poster for' or similar prefix"""
    return re.sub(r'^Poster for ', '', raw_title, flags=re.IGNORECASE).strip()


def scrape_imdb_metadata(imdb_id):
    """
    Scrape genre and country from IMDb movie page as fallback
    """
    url = f"https://www.imdb.com/title/tt{imdb_id}/"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract Genres
        genres = []
        genre_section = soup.find_all('a', {'class': 'ipc-chip'})
        for chip in genre_section:
            span = chip.find('span', {'class': 'ipc-chip__text'})
            if span:
                genres.append(span.text.strip())
        
        # Extract Country
        country = None
        country_li = soup.find('li', {'data-testid': 'title-details-origin'})
        if country_li:
            country_links = country_li.find_all('a')
            if country_links:
                country = ', '.join([link.text.strip() for link in country_links])
        
        return {
            'genre': ', '.join(genres) if genres else None,
            'country': country
        }
        
    except Exception as e:
        print(f"Scraping failed for tt{imdb_id}: {str(e)}")
        return {'genre': None, 'country': None}


def looks_like_non_movie_title(title):
    """
    Heuristic to detect podcast/episode-like titles from IMDb
    """
    if not title:
        return False
    lower_title = title.lower()
    # Common patterns indicating podcast or episode-like titles
    indicators = ['podcast', 'episode', ' ep.', ' ep ', ' audio', ' casting', 'reviewcast', 'review cast', 'show', 'interview']
    # Also reject quote marks that sometimes surround episode titles
    if any(indicator in lower_title for indicator in indicators):
        return True
    if '"' in title or '“' in title or '”' in title:
        return True
    return False


def get_movie_imdb_metadata(movie):
    """
    Main enrichment function with IMDbPY + web scraping fallback
    Filters out non-movie content (podcasts, TV episodes, etc.)
    """
    raw_title = movie.get("title")
    letterboxd_year = movie.get("year")
    title = clean_movie_title(raw_title)
    
    try:
        # Step 1: Search using IMDbPY
        results = ia.search_movie(title)
        movie_obj = None
        
        # Filter out excluded kinds and try to match by year
        for candidate in results:
            kind = candidate.get("kind")
            candidate_title = candidate.get("title", "")
            
            # Skip if kind is in excluded list
            if kind in EXCLUDED_KINDS:
                print(f"Skipping {candidate_title} - kind: {kind}")
                continue
            
            # Skip suspicious titles heuristically
            if looks_like_non_movie_title(candidate_title):
                print(f"Skipping suspicious title: {candidate_title}")
                continue
            
            # Only accept movies with matching year
            if kind == "movie" and "year" in candidate.keys():
                if str(candidate["year"]) == str(letterboxd_year):
                    movie_obj = candidate
                    print(f"✓ Matched by year: {candidate_title} ({candidate.get('year')})")
                    break
        
        # Fallback: first movie match (still excluding non-movies and suspicious titles)
        if not movie_obj:
            for candidate in results:
                kind = candidate.get("kind")
                candidate_title = candidate.get("title", "")
                
                if kind in EXCLUDED_KINDS:
                    continue
                if looks_like_non_movie_title(candidate_title):
                    continue
                if kind == "movie":
                    movie_obj = candidate
                    print(f"⚠ Year mismatch fallback: {candidate_title} ({candidate.get('year')})")
                    break
        
        if not movie_obj:
            return {"error": "No matching movie found in IMDb (or only non-movie results)"}
        
        movie_id = movie_obj.movieID
        imdb_url = f"https://www.imdb.com/title/tt{movie_id}/"
        
        # Step 2: Get basic details from IMDbPY
        movie_details = ia.get_movie(movie_id, info=['main', 'genres', 'countries'])
        
        # Double-check kind and suspicious title after fetching full details
        if movie_details.get('kind') in EXCLUDED_KINDS:
            return {"error": f"Filtered out: {movie_details.get('kind')} type content"}
        if looks_like_non_movie_title(movie_details.get('title')):
            return {"error": "Filtered out due to suspicious title format"}
        
        genre_imdbpy = ", ".join(movie_details.get("genres", [])) if movie_details.get("genres") else None
        country_imdbpy = ", ".join(movie_details.get("countries", [])) if movie_details.get("countries") else None
        
        # Step 3: If missing genre or country, scrape from web
        if not genre_imdbpy or not country_imdbpy:
            print(f"Missing data for {title}, scraping IMDb page...")
            scraped = scrape_imdb_metadata(movie_id)
            genre = genre_imdbpy or scraped.get('genre')
            country = country_imdbpy or scraped.get('country')
        else:
            genre = genre_imdbpy
            country = country_imdbpy
        
        return {
            "title_imdb": movie_details.get("title"),
            "year_imdb": movie_details.get("year"),
            "country": country,
            "genre": genre,
            "imdb_url": imdb_url
        }
        
    except Exception as e:
        return {"error": str(e)}


def batch_enrich_movies(movie_list):
    """
    Enrich a list of movies with IMDb metadata
    """
    enriched = []
    for i, movie in enumerate(movie_list, 1):
        print(f"\n[{i}/{len(movie_list)}] Enriching: {movie.get('title')}")
        meta = get_movie_imdb_metadata(movie)
        full_record = movie.copy()
        full_record.update(meta)
        enriched.append(full_record)
        time.sleep(1.5)  # Rate limiting - adjust as needed
    
    # Summary stats
    success_count = len([m for m in enriched if 'error' not in m])
    error_count = len([m for m in enriched if 'error' in m])
    print(f"\n{'='*50}")
    print(f"Enrichment Complete!")
    print(f"Success: {success_count} | Errors: {error_count}")
    print(f"{'='*50}\n")
    
    return enriched
