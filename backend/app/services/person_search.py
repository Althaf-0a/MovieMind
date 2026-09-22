import math
import re
import pandas as pd
from app.services.data_store import movies_master_df, movie_cast_df, movie_directors_df

def format_movie_result(row):
    return {
        "tmdbId": int(row['tmdbId']),
        "title": row['title'],
        "release_year": int(row['release_year']) if not math.isnan(row['release_year']) else None,
        "genres_text": row['genres_text'],
        "vote_average": float(row['vote_average']),
        "vote_count": int(row['vote_count']),
        "popularity": float(row['popularity']),
        "poster_path": row['poster_path'] if isinstance(row['poster_path'], str) else None
    }

def normalize_name(name_str):
    """Normalize name for robust matching: lowercase, remove punctuation, remove extra spaces."""
    if pd.isna(name_str) or not isinstance(name_str, str):
        return ""
    # Lowercase
    s = name_str.lower()
    # Remove punctuation
    s = re.sub(r"[^\w\s]", "", s)
    # Remove extra spaces
    s = " ".join(s.split())
    return s

# Create a normalized version of the names in the dataframes ONCE to speed up searching
if 'normalized_actor_name' not in movie_cast_df.columns:
    movie_cast_df['normalized_actor_name'] = movie_cast_df['actor_name'].apply(normalize_name)
    
if 'normalized_director_name' not in movie_directors_df.columns:
    movie_directors_df['normalized_director_name'] = movie_directors_df['director_name'].apply(normalize_name)


def search_people(query: str, role: str = 'all', limit: int = 50):
    query = query.strip()
    if not query:
        return []
        
    from app.services.query_resolver import resolve_actor, resolve_director
    
    matched_tmdb_ids = set()
    
    # Search Actors
    if role in ['actor', 'all']:
        res = resolve_actor(query)
        if res["matched"] and res["resolved"]:
            actor_norm = normalize_name(res["resolved"])
            actor_mask = movie_cast_df['normalized_actor_name'] == actor_norm
            matched_tmdb_ids.update(movie_cast_df.loc[actor_mask, 'tmdbId'].tolist())
            
    # Search Directors
    if role in ['director', 'all']:
        res = resolve_director(query)
        if res["matched"] and res["resolved"]:
            director_norm = normalize_name(res["resolved"])
            director_mask = movie_directors_df['normalized_director_name'] == director_norm
            matched_tmdb_ids.update(movie_directors_df.loc[director_mask, 'tmdbId'].tolist())
            
    if not matched_tmdb_ids:
        return []
        
    # Filter master dataset
    movies_mask = movies_master_df['tmdbId'].isin(matched_tmdb_ids)
    matches = movies_master_df[movies_mask].copy()
    
    # Sort the results by popularity so the most famous movies with that person show first
    matches = matches.sort_values(by='popularity', ascending=False).head(limit)
    
    results = []
    for _, row in matches.iterrows():
        results.append(format_movie_result(row))
        
    return results
