from fastapi import APIRouter, Query
from typing import Optional
from app.services.catalog import get_movies_catalog

router = APIRouter()

@router.get("/")
def get_movies_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=50, description="Items per page"),
    genre: Optional[str] = Query(None, description="Filter by genre (e.g., Action)"),
    year: Optional[int] = Query(None, description="Filter by exact release year"),
    min_rating: Optional[float] = Query(None, ge=0.0, le=10.0, description="Minimum average vote"),
    min_votes: Optional[int] = Query(None, ge=0, description="Minimum number of votes"),
    sort_by: Optional[str] = Query("popularity", description="Sort by: popularity, vote_average, vote_count, release_year, title")
):
    """Browse the entire master movie catalog with filters and pagination."""
    results = get_movies_catalog(
        page=page, 
        limit=limit, 
        genre=genre, 
        year=year, 
        min_rating=min_rating, 
        min_votes=min_votes, 
        sort_by=sort_by
    )
    return results

@router.get("/{tmdb_id}")
def get_movie_by_id_endpoint(tmdb_id: int):
    """Get detailed information for a specific movie from the local catalog."""
    from app.services.data_store import movies_master_df
    import math
    
    movie = movies_master_df[movies_master_df['tmdbId'] == tmdb_id]
    if movie.empty:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Movie not found in local catalog")
        
    row = movie.iloc[0]
    return {
        "id": int(row['tmdbId']),
        "title": row['title'],
        "original_title": row['original_title'],
        "release_year": int(row['release_year']) if not math.isnan(row['release_year']) else None,
        "genres": row['genres_text'],
        "overview": row['overview_text'],
        "vote_average": float(row['vote_average']),
        "vote_count": int(row['vote_count']),
        "popularity": float(row['popularity']),
        "poster_path": row['poster_path'] if isinstance(row['poster_path'], str) else None,
        "cast": row['cast_text'],
        "director": row['director_text']
    }
