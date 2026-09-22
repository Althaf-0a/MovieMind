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

def search_movies_by_title(query: str, limit: int = 50):
    query = query.strip()
    if not query:
        return []
        
    from app.services.query_resolver import resolve_title
    res = resolve_title(query)
    
    if not res["matched"] or not res["resolved"]:
        return []
        
    # Find all movies matching the resolved title (there could be remakes with the same title)
    resolved = res["resolved"].lower().strip()
    matches = movies_master_df[movies_master_df['title'].str.lower().str.strip() == resolved]
    
    if matches.empty:
        # Fallback to original_title just in case
        matches = movies_master_df[movies_master_df['original_title'].str.lower().str.strip() == resolved]
        
    if matches.empty:
        return []
        
    # Sort by popularity to get the most relevant one first
    sorted_matches = matches.sort_values(by='popularity', ascending=False).head(limit)
    
    results = []
    for _, row in sorted_matches.iterrows():
        movie_data = format_movie_result(row)
        movie_data['match_score'] = res["score"]
        movie_data['resolved_title'] = res["resolved"]
        results.append(movie_data)
        
    return results
