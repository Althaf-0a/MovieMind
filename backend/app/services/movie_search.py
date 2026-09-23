import math
from rapidfuzz import process, fuzz
from app.services.data_store import movies_master_df

def format_movie_result(row):
    """Helper to format a dataframe row into a dictionary safely."""
    return {
        "tmdbId": int(row['tmdbId']),
        "title": row['title'],
        "original_title": row['original_title'],
        "release_year": int(row['release_year']) if not math.isnan(row['release_year']) else None,
        "genres_text": row['genres_text'],
        "vote_average": float(row['vote_average']),
        "vote_count": int(row['vote_count']),
        "popularity": float(row['popularity']),
        "poster_path": row['poster_path'] if isinstance(row['poster_path'], str) else None
    }

def search_movies_by_title(query: str, min_year: int = None, max_year: int = None, limit: int = 50):
    query = query.strip()
    if not query:
        return []
        
    from app.services.query_resolver import resolve_title
    res = resolve_title(query)
    
    if not res["matched"] or not res["resolved"]:
        return []
        
    # Find the top matching movie to use as the semantic source
    resolved = res["resolved"].lower().strip()
    matches = movies_master_df[movies_master_df['title'].str.lower().str.strip() == resolved]
    
    if matches.empty:
        matches = movies_master_df[movies_master_df['original_title'].str.lower().str.strip() == resolved]
        
    if matches.empty:
        return []

    # Get the most popular exact match as our source
    best_match = matches.sort_values(by='popularity', ascending=False).iloc[0]
    source_tmdb_id = int(best_match['tmdbId'])
    
    # Perform semantic similar-movie search based on this movie's embedding
    from app.services.semantic_search import search_similar_by_tmdb_id
    results = search_similar_by_tmdb_id(source_tmdb_id, min_year, max_year, limit)
    
    return results
