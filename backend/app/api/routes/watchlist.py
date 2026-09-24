from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, WatchlistItem
from app.schemas import WatchlistItemCreate, WatchlistItemResponse
from app.services.auth import get_current_user

router = APIRouter(tags=["Watchlist"])

@router.get("/", response_model=List[WatchlistItemResponse])
def get_watchlist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id
    ).order_by(WatchlistItem.added_at.desc()).all()
    return items

from fastapi import Response

@router.post("/", response_model=WatchlistItemResponse)
def add_to_watchlist(
    item: WatchlistItemCreate, 
    response: Response,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # Check for existing item to prevent duplicates
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.tmdb_id == item.tmdb_id
    ).first()
    
    if existing:
        response.status_code = status.HTTP_200_OK
        return existing

    new_item = WatchlistItem(
        user_id=current_user.id,
        tmdb_id=item.tmdb_id,
        title=item.title,
        release_year=item.release_year,
        poster_path=item.poster_path,
        source=item.source
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    response.status_code = status.HTTP_201_CREATED
    return new_item

@router.delete("/{tmdb_id}")
def remove_from_watchlist(
    tmdb_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    item = db.query(WatchlistItem).filter(
        WatchlistItem.user_id == current_user.id,
        WatchlistItem.tmdb_id == tmdb_id
    ).first()
    
    if not item:
        # We can safely return success even if not found, or a 404.
        # User requested a clear success response or suitable response without crashing.
        return {"status": "success", "message": "Item not found or already removed"}
        
    db.delete(item)
    db.commit()
    return {"status": "success"}
