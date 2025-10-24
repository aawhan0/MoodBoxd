import wikipedia
import requests
import re
import time

def get_movie_wikipedia_metadata(title):
    try:
        # Step 1: Resolve movie's Wikipedia page (get canonical title)
        page = wikipedia.page(title)
        page_title = page.title

        # Step 2: Fetch the raw wikitext source of that page
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": page_title,
            "rvslots": "*",
            "rvprop": "content"
        }
        response = requests.get(url, params=params)
        data = response.json()
        pages = data["query"]["pages"]
        wikitext = next(iter(pages.values()))["revisions"][0]["slots"]["main"]["*"]

        # Step 3: Extract details from the infobox using regex
        def extract_field(field):
            match = re.search(rf"\|\s*{field}\s*=\s*([^\n|]+)", wikitext, re.IGNORECASE)
            return match.group(1).strip() if match else None

        country = extract_field("country")
        genre = extract_field("genre")
        year = extract_field("released") or extract_field("release_date") or extract_field("year")

        return {
            "country": country,
            "genre": genre,
            "year": year,
            "wikipedia_url": page.url
        }
    except Exception as e:
        return {"error": str(e)}

def batch_enrich_movies(movie_list):
    enriched = []
    for movie in movie_list:
        title = movie.get("title")
        if not title:
            continue
        meta = get_movie_wikipedia_metadata(title)
        full_record = movie.copy()
        full_record.update(meta)
        enriched.append(full_record)
        time.sleep(1)  # Rate limit: 1 request per second
    return enriched

# Standalone test
if __name__ == "__main__":
    print(get_movie_wikipedia_metadata("Inception"))
