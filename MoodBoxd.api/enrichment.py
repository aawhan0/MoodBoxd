from imdb import IMDb
import re
import time

# Initialize IMDbPY instance
ia = IMDb()

def clean_movie_title(raw_title):
    # Remove "Poster for" or similar prefix
    clean_title = re.sub(r'^Poster for ', '', raw_title, flags=re.IGNORECASE)
    # Extract year from parentheses if present
    year_match = re.search(r'\((\d{4})\)$', clean_title)
    year = int(year_match.group(1)) if year_match else None
    # Remove year from title for searching
    title_without_year = re.sub(r' *\(\d{4}\)$', '', clean_title).strip()
    return title_without_year, year

def get_movie_imdb_metadata(raw_title):
    title, year = clean_movie_title(raw_title)
    try:
        # Search movies using IMDbPY
        search_results = ia.search_movie(title)
        movie = None
        # Try to find movie that matches the year (if year known)
        for candidate in search_results:
            if year:
                if 'year' in candidate.keys() and candidate['year'] == year:
                    movie = candidate
                    break
            else:
                movie = candidate
                break
        if not movie:
            return {"error": "No matching movie found in IMDb"}
        # Fetch full movie info
        ia.update(movie)
        country = movie.get('countries', [None])[0]
        genre = ', '.join(movie.get('genres', [])) if movie.get('genres') else None
        year = movie.get('year', year)
        imdb_id = movie.movieID
        imdb_url = f"https://www.imdb.com/title/tt{imdb_id}/" if imdb_id else None

        return {
            "title_imdb": movie.get('title'),
            "year": year,
            "country": country,
            "genre": genre,
            "imdb_url": imdb_url
        }
    except Exception as e:
        return {"error": str(e)}

def batch_enrich_movies(movie_list):
    enriched = []
    for movie in movie_list:
        raw_title = movie.get('title')
        if not raw_title:
            continue
        meta = get_movie_imdb_metadata(raw_title)
        full_record = movie.copy()
        full_record.update(meta)
        enriched.append(full_record)
        time.sleep(1)  # prevent overwhelming IMDbPY / IMDb servers
    return enriched
