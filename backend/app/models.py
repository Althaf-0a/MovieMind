from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    watchlist = relationship("WatchlistItem", back_populates="user", cascade="all, delete-orphan")

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    tmdb_id = Column(Integer, index=True, nullable=False)
    title = Column(String, nullable=False)
    release_year = Column(Integer, nullable=True)
    poster_path = Column(String, nullable=True)
    source = Column(String, nullable=False)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="watchlist")

    __table_args__ = (
        UniqueConstraint('user_id', 'tmdb_id', name='uq_user_tmdb'),
    )
