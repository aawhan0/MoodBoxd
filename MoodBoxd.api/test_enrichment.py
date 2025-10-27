# test_enrichment.py
from enrichment import batch_enrich_movies

test_movies = [
    {"title": "It's What's Inside", "year": "2024"},
    {"title": "Don't Breathe", "year": "2016"},
    {"title": "Harry Potter and the Deathly Hallows: Part 2", "year": "2011"}
]

enriched = batch_enrich_movies(test_movies)

for movie in enriched:
    if 'error' in movie:
        print(f"❌ {movie['title']}: {movie['error']}")
    else:
        print(f"✅ {movie['title_imdb']} ({movie['year_imdb']}) - {movie['genre']}")
