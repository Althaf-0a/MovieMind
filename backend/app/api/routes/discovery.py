from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.services.hybrid_discovery import hybrid_search

router = APIRouter(tags=["Discovery"])

class DiscoveryRequest(BaseModel):
    plot: Optional[str] = None
    actor: Optional[str] = None
    director: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_rating: Optional[float] = None
    top_n: int = 10

class MatchReason(BaseModel):
    reason: str

class DiscoveryResult(BaseModel):
    id: int
    title: str
    original_title: str
    release_year: Optional[int] = None
    genres_text: str
    overview_text: str
    vote_average: float
    vote_count: int
    popularity: float
    poster_path: Optional[str] = None
    final_score: float
    plot_similarity: float
    actor_match: bool
    director_match: bool
    genre_match: bool
    match_reasons: List[str]

class DiscoveryResponse(BaseModel):
    query: dict
    resolved_queries: dict = {}
    total_results: int
    results: List[DiscoveryResult]

@router.post("/search", response_model=DiscoveryResponse)
async def search_discovery(request: DiscoveryRequest):
    if not any([request.plot, request.actor, request.director, request.genre, request.year, request.min_year, request.max_year, request.min_rating]):
        raise HTTPException(status_code=400, detail="At least one meaningful search criterion must be provided.")
        
    try:
        results, resolved_info = hybrid_search(
            plot=request.plot,
            actor=request.actor,
            director=request.director,
            genre=request.genre,
            year=request.year,
            min_year=request.min_year,
            max_year=request.max_year,
            min_rating=request.min_rating,
            top_n=request.top_n
        )
        
        return DiscoveryResponse(
            query=request.dict(),
            resolved_queries=resolved_info,
            total_results=len(results),
            results=results
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
