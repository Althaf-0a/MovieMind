from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.watchlist import router as watchlist_router

from app.database import engine
from app import models

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MovieMind API",
    description="Backend API for MovieMind, a full-stack AI movie recommendation system.",
    version="0.1.0",
)

# Allow the Vite React app to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health checks live under /api, for example GET /api/health
app.include_router(health_router, prefix="/api")

# Authentication endpoints
app.include_router(auth_router, prefix="/api/auth")

# Watchlist endpoints
app.include_router(watchlist_router, prefix="/api/watchlist")

# Movie recommendations endpoint
from app.api.routes.recommendations import router as recommendations_router
app.include_router(recommendations_router, prefix="/api/recommendations", tags=["Recommendations"])

# Search endpoints
from app.api.routes.search import router as search_router
app.include_router(search_router, prefix="/api/search", tags=["Search"])

# Catalog endpoints
from app.api.routes.movies import router as movies_router
app.include_router(movies_router, prefix="/api/movies", tags=["Catalog"])

# TMDB endpoints
from app.api.routes.tmdb import router as tmdb_router
app.include_router(tmdb_router, prefix="/api/tmdb", tags=["TMDB"])

# Discovery endpoints
from app.api.routes.discovery import router as discovery_router
app.include_router(discovery_router, prefix="/api/discovery", tags=["Discovery"])
