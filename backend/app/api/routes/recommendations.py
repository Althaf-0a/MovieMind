from fastapi import APIRouter, HTTPException, Query
from app.services.recommender import recommend_movies

router = APIRouter()

# This route acts as the bridge connecting the frontend to the ML recommendation service.
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
    
    # The recommender returns a dictionary with an 'error' key if the movie isn't found
    if isinstance(results, dict) and "error" in results:
        raise HTTPException(status_code=404, detail=results["error"])
        
    return {
        "requested_movie": movie_title,
        "recommendations": results
    }
