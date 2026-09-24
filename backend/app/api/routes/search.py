from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.services.movie_search import search_movies_by_title
from app.services.person_search import search_people
from app.services.plot_search import search_by_plot

router = APIRouter()

@router.get("/movies")
async def search_movies_endpoint(
    query: str = Query(..., min_length=1, description="Movie title to search for"),
    min_year: Optional[int] = Query(None),
    max_year: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50, description="Max number of results to return")
):
    """Search for movies by their title using robust local+TMDB fallback."""
    results = await search_movies_by_title(query, min_year, max_year, limit)
    return results

@router.get("/people")
def search_people_endpoint(
    query: str = Query(..., min_length=1, description="Name of the person (actor or director)"),
    role: str = Query("all", pattern="^(actor|director|all)$", description="Role to search for: actor, director, or all"),
    min_year: Optional[int] = Query(None),
    max_year: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=50, description="Max number of results to return")
):
    """Search for movies starring or directed by a specific person."""
    results = search_people(query, role, min_year, max_year, limit)
    return results

from app.services.semantic_search import search_plot_semantic

@router.get("/plot")
def search_plot_endpoint(
    query: str = Query(..., min_length=1, description="Natural language description of the plot"),
    limit: int = Query(10, ge=1, le=20, description="Max number of results to return")
):
    """Find movies by typing a plot description using Semantic Similarity."""
    results = search_plot_semantic(query, limit)
    return results
