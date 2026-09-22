from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Simple check that the MovieMind backend is up."""
    return {
        "status": "ok",
        "message": "MovieMind backend is running",
    }
