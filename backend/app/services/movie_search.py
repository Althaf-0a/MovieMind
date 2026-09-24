import math
import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz
from app.services.data_store import movies_master_df
from app.services.query_resolver import resolve_title
from app.services import semantic_search
from app.services.tmdb_service import search_movies as tmdb_search_movies, get_movie_details as tmdb_get_movie_details

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

async def search_movies_by_title(query: str, min_year: int = None, max_year: int = None, limit: int = 50):
    query = query.strip()
    if not query:
        return {"resolved_movie": None, "results": []}
        
    res = resolve_title(query)
    
    # 1. Try local resolution first
    if res["matched"] and res["resolved"]:
        resolved = res["resolved"].lower().strip()
        matches = movies_master_df[movies_master_df['title'].str.lower().str.strip() == resolved]
        
        if matches.empty:
            matches = movies_master_df[movies_master_df['original_title'].str.lower().str.strip() == resolved]
            
        if not matches.empty:
            best_match = matches.sort_values(by='popularity', ascending=False).iloc[0]
            source_tmdb_id = int(best_match['tmdbId'])
            
            results = semantic_search.search_similar_by_tmdb_id(source_tmdb_id, min_year, max_year, limit)
            
            return {
                "resolved_movie": {
                    "title": best_match['title'],
                    "release_year": int(best_match['release_year']) if pd.notna(best_match['release_year']) else None,
                    "tmdb_id": source_tmdb_id,
                    "source": "LOCAL"
                },
                "results": results
            }

    # 2. TMDB Fallback
    try:
        tmdb_res = await tmdb_search_movies(query, page=1)
        if tmdb_res and tmdb_res.get("results") and len(tmdb_res["results"]) > 0:
            best_tmdb = tmdb_res["results"][0]
            tmdb_id = best_tmdb["id"]
            title = best_tmdb.get("title", query)
            release_date = best_tmdb.get("release_date", "")
            release_year = int(release_date.split('-')[0]) if release_date else None
            
            # Get full details to ensure we have an overview
            details = await tmdb_get_movie_details(tmdb_id)
            overview = details.get("overview", "")
            
            if not overview:
                return {"resolved_movie": None, "results": []}
                
            # Semantic Search
            if semantic_search.semantic_model is None or semantic_search.faiss_index is None:
                semantic_search.init_semantic_search()
                
            if semantic_search.semantic_model is None or semantic_search.faiss_index is None:
                return {"resolved_movie": None, "results": []}
                
            vec = semantic_search.semantic_model.encode([overview])[0]
            vec = vec / np.linalg.norm(vec)
            vec = np.array([vec]).astype('float32')
            
            # Exclude this TMDB movie if it happens to exist locally
            top_k = limit + 5 
            distances, indices = semantic_search.faiss_index.search(vec, top_k)
            
            results = []
            master_df_indexed = movies_master_df.set_index('tmdbId')
            
            for score, idx in zip(distances[0], indices[0]):
                if idx == -1: continue
                cand_tmdb_id = int(semantic_search.embedding_index.iloc[idx]['tmdbId'])
                
                # Exclusion
                if cand_tmdb_id == tmdb_id:
                    continue
                    
                if cand_tmdb_id in master_df_indexed.index:
                    row = master_df_indexed.loc[cand_tmdb_id]
                    
                    if min_year and (pd.isna(row.get('release_year')) or row['release_year'] < min_year):
                        continue
                    if max_year and (pd.isna(row.get('release_year')) or row['release_year'] > max_year):
                        continue
                        
                    results.append({
                        "tmdbId": cand_tmdb_id,
                        "title": row['title'],
                        "overview_text": row['overview_text'] if 'overview_text' in row else '',
                        "release_year": int(row['release_year']) if pd.notna(row.get('release_year')) else None,
                        "genres_text": row['genres_text'] if 'genres_text' in row else '',
                        "vote_average": float(row['vote_average']) if 'vote_average' in row else 0.0,
                        "vote_count": int(row['vote_count']) if 'vote_count' in row else 0,
                        "poster_path": row['poster_path'] if 'poster_path' in row else '',
                        "similarity_score": float(score),
                        "_source": 'MovieMind Database'
                    })
                    
                    if len(results) >= limit:
                        break
                        
            return {
                "resolved_movie": {
                    "title": title,
                    "release_year": release_year,
                    "tmdb_id": tmdb_id,
                    "source": "TMDB"
                },
                "results": results
            }
    except Exception as e:
        print(f"TMDB fallback failed: {e}")
        pass
        
    return {"resolved_movie": None, "results": []}
