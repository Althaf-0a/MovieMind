from fastapi import APIRouter, Query, Path, HTTPException
from typing import Optional

from app.services.tmdb_service import search_movies, get_movie_details, search_people

router = APIRouter()

@router.get("/movies/search")
async def search_tmdb_movies_endpoint(
    query: str = Query(..., min_length=1, description="Movie title to search on TMDB"),
    page: int = Query(1, ge=1, description="Page number for pagination")
):
    """Search for movies on TMDB."""
    try:
        results = await search_movies(query, page=page)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from TMDB: {str(e)}")

from app.services.movie_discovery import get_related_movies

@router.get("/movies/{tmdb_id}")
async def get_tmdb_movie_endpoint(
    tmdb_id: int = Path(..., ge=1, description="Valid TMDB Movie ID")
):
    """Get details for a specific movie from TMDB."""
    try:
        movie = await get_movie_details(tmdb_id)
        return movie
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching movie details from TMDB: {str(e)}")

@router.get("/movies/{tmdb_id}/related")
async def get_related_movies_endpoint(
    tmdb_id: int = Path(..., ge=1, description="Valid TMDB Movie ID")
):
    """Discover related movies based on relationships."""
    try:
        data = await get_related_movies(tmdb_id)
        return data
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching related movies: {str(e)}")

@router.get("/people/search")
async def search_tmdb_people_endpoint(
    query: str = Query(..., min_length=1, description="Person name to search on TMDB"),
    page: int = Query(1, ge=1, description="Page number for pagination")
):
    """Search for people (actors, directors, etc.) on TMDB."""
    try:
        results = await search_people(query, page=page)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data from TMDB: {str(e)}")
