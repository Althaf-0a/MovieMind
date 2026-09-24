import numpy as np
import pandas as pd
import asyncio
from app.services import semantic_search
from app.services.data_store import movies_master_df
from app.services.tmdb_service import get_movie_details

# In-memory cache for dynamically generated TMDB embeddings
_tmdb_embedding_cache = {}

async def get_personalized_recommendations(watchlist_items, limit=20):
    # Ensure lazy initialization of the semantic engine happens
    if semantic_search.semantic_model is None:
        semantic_search.init_semantic_search()
        
    if not watchlist_items or semantic_search.faiss_index is None or semantic_search.semantic_model is None:
        return []
        
    vectors = []
    watchlist_tmdb_ids = set()
    
    for item in watchlist_items:
        tmdb_id = item.tmdb_id
        watchlist_tmdb_ids.add(tmdb_id)
        
        # Check if in local FAISS DB
        matching_indices = semantic_search.embedding_index[semantic_search.embedding_index['tmdbId'] == tmdb_id].index.tolist()
        
        if matching_indices:
            # We have it locally
            idx = matching_indices[0]
            vec = semantic_search.movie_embeddings[idx]
            vectors.append(vec)
        else:
            # TMDB-only movie, check cache
            if tmdb_id in _tmdb_embedding_cache:
                vectors.append(_tmdb_embedding_cache[tmdb_id])
            else:
                # Fetch dynamically
                try:
                    details = await get_movie_details(tmdb_id)
                    overview = details.get('overview', '')
                    if overview:
                        # Encode it
                        vec = semantic_search.semantic_model.encode([overview])[0]
                        # Normalize single vector
                        vec = vec / np.linalg.norm(vec)
                        _tmdb_embedding_cache[tmdb_id] = vec
                        vectors.append(vec)
                except Exception as e:
                    print(f"Failed to fetch/encode TMDB movie {tmdb_id}: {e}")
                    
    if not vectors:
        return []
        
    # Aggregate and normalize
    preference_vector = np.mean(vectors, axis=0)
    # The L2 normalization ensures FAISS cosine similarity works properly
    preference_vector = preference_vector / np.linalg.norm(preference_vector)
    # Reshape for FAISS (needs 2D array: 1 x dimension)
    preference_vector = np.array([preference_vector]).astype('float32')
    
    # Search
    # Fetch extra candidates to account for exclusion of watchlist items
    top_k = limit + len(watchlist_tmdb_ids) + 10
    distances, indices = semantic_search.faiss_index.search(preference_vector, top_k)
    
    # Format results
    results = []
    master_df_indexed = movies_master_df.set_index('tmdbId')
    
    for score, idx in zip(distances[0], indices[0]):
        if idx == -1: continue # FAISS empty hit
        if len(results) >= limit: break
            
        cand_tmdb_id = int(semantic_search.embedding_index.iloc[idx]['tmdbId'])
        
        if cand_tmdb_id in watchlist_tmdb_ids:
            continue
            
        if cand_tmdb_id in master_df_indexed.index:
            row = master_df_indexed.loc[cand_tmdb_id]
            
            # Map back to our normalized schema
            results.append({
                "tmdbId": cand_tmdb_id,
                "id": cand_tmdb_id,
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
            
    return results
