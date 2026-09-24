from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

from typing import Optional
from datetime import datetime

class WatchlistItemCreate(BaseModel):
    tmdb_id: int
    title: str
    release_year: Optional[int] = None
    poster_path: Optional[str] = None
    source: str

class WatchlistItemResponse(BaseModel):
    id: int
    tmdb_id: int
    title: str
    release_year: Optional[int]
    poster_path: Optional[str]
    source: str
    added_at: datetime

    class Config:
        from_attributes = True

