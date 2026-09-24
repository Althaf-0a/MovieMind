from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.services.recommender import recommend_movies
from app.database import get_db
from app.api.routes.auth import get_current_user
from app.models import User, WatchlistItem
from app.services.recommendations_service import get_personalized_recommendations

router = APIRouter()

@router.get("/personalized")
async def get_personalized(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns personalized movie recommendations based on the user's watchlist.
    """
    watchlist_items = db.query(WatchlistItem).filter(WatchlistItem.user_id == current_user.id).all()
    
    if not watchlist_items:
        return []
        
    try:
        recommendations = await get_personalized_recommendations(watchlist_items, limit=20)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("")
def get_recommendations(
    movie_title: str = Query(..., description="Title of the movie to get recommendations for"),
    top_n: int = Query(10, ge=1, le=20, description="Number of recommendations to return (1-20)")
):
    """
    Get movie recommendations based on a given movie title.
    """
    # Call the ML service
    results = recommend_movies(movie_title, top_n)
    
    if isinstance(results, dict) and "error" in results:
        raise HTTPException(status_code=404, detail=results["error"])
        
    return {
        "requested_movie": movie_title,
        "recommendations": results
    }
