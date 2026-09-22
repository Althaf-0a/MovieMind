import math
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from app.services.data_store import movies_master_df, movie_cast_df, movie_directors_df

def normalize_text(text: str):
    if not text: return ""
    return str(text).lower().strip()

def get_movies_with_actor(actor_name: str):
    if not actor_name: return set()
    actor_norm = normalize_text(actor_name)
    matches = movie_cast_df[movie_cast_df['actor_name'].str.lower().str.strip() == actor_norm]
    return set(matches['tmdbId'].unique())

def get_movies_with_director(director_name: str):
    if not director_name: return set()
    dir_norm = normalize_text(director_name)
    matches = movie_directors_df[movie_directors_df['director_name'].str.lower().str.strip() == dir_norm]
    return set(matches['tmdbId'].unique())

def hybrid_search(plot: str=None, actor: str=None, director: str=None, genre: str=None, year: int=None, min_rating: float=None, top_n: int=10):
    # Import inside to avoid circular deps and rely on semantic_search being loaded
    import app.services.semantic_search as semantic_search
    from app.services.query_resolver import resolve_actor, resolve_director
    semantic_search.init_semantic_search()
    
    # 0. Resolve Input Queries
    resolved_actor_name = None
    if actor:
        actor_res = resolve_actor(actor)
        if actor_res["matched"] and not actor_res["ambiguous"]:
            resolved_actor_name = actor_res["resolved"]
        else:
            resolved_actor_name = actor # fallback to exact string if unresolved
            
    resolved_director_name = None
    if director:
        dir_res = resolve_director(director)
        if dir_res["matched"] and not dir_res["ambiguous"]:
            resolved_director_name = dir_res["resolved"]
        else:
            resolved_director_name = director

    # 2. Hard Filters pre-computation (Actor & Director are constraints here)
    actor_movies = get_movies_with_actor(resolved_actor_name) if resolved_actor_name else set()
    director_movies = get_movies_with_director(resolved_director_name) if resolved_director_name else set()
    
    seed_ids = set()
    constrained_by_person = False
    
    if actor and director:
        seed_ids = actor_movies.intersection(director_movies)
        if not seed_ids:
            seed_ids = actor_movies.union(director_movies)
        constrained_by_person = True
    elif actor:
        seed_ids = actor_movies
        constrained_by_person = True
    elif director:
        seed_ids = director_movies
        constrained_by_person = True
    
    # 1. Base Candidate Generation
    candidates = {} # tmdbId -> plot_similarity (or 0)
    
    if plot and plot.strip():
        query_vector = semantic_search.semantic_model.encode([plot.strip()])
        similarity_scores = cosine_similarity(query_vector, semantic_search.movie_embeddings).flatten()
        
        if constrained_by_person:
            # Evaluate ONLY movies matching the person(s)
            for tmdb_id in seed_ids:
                idx_series = semantic_search.embedding_index.index[semantic_search.embedding_index['tmdbId'] == tmdb_id].tolist()
                if idx_series:
                    idx = idx_series[0]
                    score = float(similarity_scores[idx])
                    candidates[tmdb_id] = score
        else:
            # Plot only, no person constraints. Take top 500 semantic matches.
            scores_with_indices = [(idx, float(score)) for idx, score in enumerate(similarity_scores) if score > 0.0]
            scores_with_indices.sort(key=lambda x: x[1], reverse=True)
            scores_with_indices = scores_with_indices[:500]
            for idx, score in scores_with_indices:
                tmdb_id = semantic_search.embedding_index.iloc[idx]['tmdbId']
                candidates[tmdb_id] = score
    else:
        # No plot provided.
        if constrained_by_person:
            for tmdb_id in seed_ids:
                candidates[tmdb_id] = 0.0
        else:
            # No plot, no actor, no director. Fallback to all.
            for tmdb_id in movies_master_df['tmdbId'].unique():
                candidates[tmdb_id] = 0.0

    # Weights definition
    # Maximum possible score based on provided inputs
    plot_w = 60 if plot else 0
    actor_w = 20 if actor else 0
    director_w = 10 if director else 0
    genre_w = 5 if genre else 0
    year_w = 5 if year else 0
    
    total_w = plot_w + actor_w + director_w + genre_w + year_w
    if total_w == 0:
        total_w = 1 # Fallback, shouldn't happen due to router validation
        
    master_indexed = movies_master_df.set_index('tmdbId')
    
    results_list = []
    
    # 3. Score and Filter candidates
    for tmdb_id, plot_score in candidates.items():
        if tmdb_id not in master_indexed.index:
            continue
            
        row = master_indexed.loc[tmdb_id]
        
        # Hard Filter: Rating
        vote_avg = row['vote_average'] if not pd.isna(row['vote_average']) else 0.0
        if min_rating and vote_avg < min_rating:
            continue
            
        # Hard Filter: Year
        rel_year = row['release_year'] if not pd.isna(row['release_year']) else None
        if year and rel_year != year:
            continue
            
        # Hard Filter: Genre
        genres_text = row['genres_text'] if not pd.isna(row['genres_text']) else ""
        if genre:
            if genre.lower() not in genres_text.lower():
                continue
                
        # Calculate score
        score_points = 0.0
        reasons = []
        
        # Plot
        if plot:
            # normalize plot score slightly to represent a percentage of the 60 points
            # A score of 1.0 = 60 points. Negative scores already filtered.
            norm_plot = max(0, min(1.0, plot_score))
            score_points += norm_plot * plot_w
            if norm_plot > 0.4:
                reasons.append("Strong plot similarity")
            elif norm_plot > 0.2:
                reasons.append("Moderate plot similarity")
                
        # Actor
        actor_match = False
        if resolved_actor_name:
            if tmdb_id in actor_movies:
                actor_match = True
                score_points += actor_w
                reasons.append(f"Starring {resolved_actor_name}")
                
        # Director
        director_match = False
        if resolved_director_name:
            if tmdb_id in director_movies:
                director_match = True
                score_points += director_w
                reasons.append(f"Directed by {resolved_director_name}")
                
        # Genre
        genre_match = False
        if genre:
            genre_match = True
            score_points += genre_w
            reasons.append(f"Genre match: {genre}")
            
        # Year
        if year:
            score_points += year_w
            reasons.append(f"Released in {year}")
            
        # Calculate final normalized score
        final_score = (score_points / total_w) * 100.0
        
        # Strictly cap the final score to be between 0.0 and 100.0
        final_score = min(100.0, max(0.0, final_score))
        
        pop = row['popularity'] if not pd.isna(row['popularity']) else 0.0
        
        results_list.append({
            "id": int(tmdb_id),
            "title": row['title'],
            "original_title": row['original_title'],
            "release_year": rel_year,
            "genres_text": genres_text,
            "overview_text": row['overview_text'] if not pd.isna(row['overview_text']) else "",
            "vote_average": vote_avg,
            "vote_count": int(row['vote_count']) if not pd.isna(row['vote_count']) else 0,
            "popularity": pop,
            "poster_path": row['poster_path'] if not pd.isna(row['poster_path']) else None,
            "final_score": final_score,
            "plot_similarity": round(plot_score, 3) if plot else 0.0,
            "actor_match": actor_match,
            "director_match": director_match,
            "genre_match": genre_match,
            "match_reasons": reasons,
            "_sort_pop": pop # Hidden field for sorting
        })

    # Sort descending by final score first, then popularity as a tie-breaker
    results_list.sort(key=lambda x: (x['final_score'], x['_sort_pop']), reverse=True)
    
    # Clean up the hidden sort key
    for r in results_list:
        del r['_sort_pop']
    
    # Expose resolution info
    resolved_info = {}
    if actor:
        resolved_info["actor"] = actor_res
    if director:
        resolved_info["director"] = dir_res
        
    return results_list[:top_n], resolved_info
