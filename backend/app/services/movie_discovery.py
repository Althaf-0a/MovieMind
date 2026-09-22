import asyncio
import httpx
from collections import defaultdict
from app.services.tmdb_service import fetch_with_retries, TMDB_BASE_URL, HEADERS, TIMEOUT, format_movie

async def get_full_movie_data(tmdb_id: int):
    url = f"{TMDB_BASE_URL}/3/movie/{tmdb_id}"
    params = {
        "append_to_response": "credits,keywords,similar,recommendations"
    }
    return await fetch_with_retries(None, url, HEADERS, params)

async def get_collection(collection_id: int):
    url = f"{TMDB_BASE_URL}/3/collection/{collection_id}"
    try:
        return await fetch_with_retries(None, url, HEADERS)
    except:
        return None

async def discover_movies(params: dict):
    url = f"{TMDB_BASE_URL}/3/discover/movie"
    params["include_adult"] = "false"
    params["sort_by"] = "popularity.desc"
    try:
        data = await fetch_with_retries(None, url, HEADERS, params)
        return data.get("results", [])
    except:
        return []

async def get_related_movies(tmdb_id: int):
    source_movie_raw = await get_full_movie_data(tmdb_id)
    
    # Parse attributes
    collection = source_movie_raw.get("belongs_to_collection")
    companies = [c["id"] for c in source_movie_raw.get("production_companies", [])][:2] # top 2 companies
    genres = [g["id"] for g in source_movie_raw.get("genres", [])]
    
    credits = source_movie_raw.get("credits", {})
    cast = [c for c in credits.get("cast", [])][:3] # top 3 cast
    director = next((c for c in credits.get("crew", []) if c.get("job") == "Director"), None)
    
    keywords_data = source_movie_raw.get("keywords", {}).get("keywords", [])
    keywords = [k["id"] for k in keywords_data][:5] # top 5 keywords
    
    similar_movies = source_movie_raw.get("similar", {}).get("results", [])
    recommendations = source_movie_raw.get("recommendations", {}).get("results", [])
    
    # Parallel candidate fetching
    tasks = []
    
    if collection:
        tasks.append(get_collection(collection["id"]))
        
    if companies:
        tasks.append(discover_movies({"with_companies": "|".join(map(str, companies))}))
        
    if cast:
        cast_ids = [c["id"] for c in cast]
        tasks.append(discover_movies({"with_cast": ",".join(map(str, cast_ids))}))
        
    if director:
        tasks.append(discover_movies({"with_crew": director["id"]}))
        
    if keywords:
        tasks.append(discover_movies({"with_keywords": "|".join(map(str, keywords))}))
        
    fetched_results = []
    for task in tasks:
        fetched_results.append(await task)
    
    # Process results
    candidates = {}
    
    def add_candidate(movie_obj, score_add, reason):
        m_id = movie_obj.get("id")
        if not m_id or m_id == tmdb_id:
            return
        if m_id not in candidates:
            candidates[m_id] = {
                "movie": format_movie(movie_obj),
                "score": 0,
                "reasons": set(),
                "genres": movie_obj.get("genre_ids", [])
            }
            
            # Baseline genre score check
            shared_genres = set(candidates[m_id]["genres"]).intersection(set(genres))
            if shared_genres:
                candidates[m_id]["score"] += len(shared_genres) * 5
                if len(shared_genres) > 0:
                    candidates[m_id]["reasons"].add("Shared genres")
                    
        candidates[m_id]["score"] += score_add
        candidates[m_id]["reasons"].add(reason)

    # 1. TMDB Similar / Recommendations
    for m in similar_movies:
        add_candidate(m, 10, "TMDB Similar")
    for m in recommendations:
        add_candidate(m, 10, "TMDB Recommendation")
        
    # 2. Process fetched tasks
    idx = 0
    if collection:
        coll_data = fetched_results[idx]
        idx += 1
        if coll_data and "parts" in coll_data:
            for m in coll_data["parts"]:
                add_candidate(m, 100, "Same franchise")
                
    if companies:
        company_movies = fetched_results[idx]
        idx += 1
        for m in company_movies:
            add_candidate(m, 15, "Shared production company")
            
    if cast:
        cast_movies = fetched_results[idx]
        idx += 1
        for m in cast_movies:
            add_candidate(m, 35, "Shared cast")
            
    if director:
        dir_movies = fetched_results[idx]
        idx += 1
        for m in dir_movies:
            add_candidate(m, 30, f"Same director")
            
    if keywords:
        kw_movies = fetched_results[idx]
        idx += 1
        for m in kw_movies:
            add_candidate(m, 10, "Shared keywords")

    # Prepare final list
    final_list = []
    for m_id, data in candidates.items():
        movie = data["movie"]
        pop = movie.get("popularity") or 0.0
        # pop tie-breaker
        final_score = data["score"] + (pop * 0.001)
        
        movie["relationship_score"] = final_score
        movie["relationship_reasons"] = list(data["reasons"])
        # Fallback for release_year
        if movie.get("release_date"):
            movie["release_year"] = movie["release_date"].split("-")[0]
        
        final_list.append(movie)
        
    # Sort by score
    final_list.sort(key=lambda x: x["relationship_score"], reverse=True)
    
    # Limit to top 20
    final_list = final_list[:20]
    
    return {
        "source_movie": format_movie(source_movie_raw),
        "related_movies": final_list,
        "relationship_summary": [m["relationship_reasons"] for m in final_list]
    }
