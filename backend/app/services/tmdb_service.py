import os
import httpx
from dotenv import load_dotenv

# Load environment variables from backend/.env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path)

TMDB_API_TOKEN = os.getenv("TMDB_API_TOKEN")
TMDB_BASE_URL = "https://api.themoviedb.org"

# Check if token exists, to prevent cryptic errors
if not TMDB_API_TOKEN:
    raise ValueError("TMDB_API_TOKEN environment variable not set. Check your backend/.env file.")

HEADERS = {
    "Authorization": f"Bearer {TMDB_API_TOKEN}",
    "accept": "application/json"
}

# Timeout for HTTP requests
TIMEOUT = 30.0

def format_movie(movie_data):
    """Extract useful fields from a TMDB movie object."""
    return {
        "id": movie_data.get("id"),
        "title": movie_data.get("title"),
        "original_title": movie_data.get("original_title"),
        "overview": movie_data.get("overview"),
        "release_date": movie_data.get("release_date"),
        "popularity": movie_data.get("popularity"),
        "vote_average": movie_data.get("vote_average"),
        "vote_count": movie_data.get("vote_count"),
        "poster_path": movie_data.get("poster_path")
    }

import asyncio

import requests

async def fetch_with_retries(client_or_url, url=None, headers=None, params=None, retries=3):
    # Support both old and new signatures
    if isinstance(client_or_url, str):
        url = client_or_url
    else:
        url = url
    
    for attempt in range(retries):
        try:
            # Use requests in a thread to bypass httpx Windows async bugs
            response = await asyncio.to_thread(
                requests.get, url, headers=headers, params=params, timeout=TIMEOUT, verify=False
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if attempt == retries - 1:
                raise RuntimeError(f"TMDB API HTTP Error: {e.response.status_code} {e.response.text}")
            await asyncio.sleep(1.0)
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                raise RuntimeError(f"TMDB API Request Error: {repr(e)}")
            await asyncio.sleep(1.0)

async def search_movies(query: str, page: int = 1):
    url = f"{TMDB_BASE_URL}/3/search/movie"
    params = {
        "query": query,
        "page": page,
        "include_adult": "false"
    }
    
    data = await fetch_with_retries(None, url, HEADERS, params)
    # Format the movie results
    formatted_results = [format_movie(m) for m in data.get("results", [])]
    return {
        "page": data.get("page"),
        "total_results": data.get("total_results"),
        "total_pages": data.get("total_pages"),
        "results": formatted_results
    }

async def get_movie_details(tmdb_id: int):
    url = f"{TMDB_BASE_URL}/3/movie/{tmdb_id}"
    params = {"append_to_response": "credits"}
    
    data = await fetch_with_retries(None, url, HEADERS, params=params)
    
    movie = format_movie(data)
    
    # Extract director and cast from credits if available
    credits = data.get("credits", {})
    crew = credits.get("crew", [])
    cast = credits.get("cast", [])
    
    directors = [member["name"] for member in crew if member.get("job") == "Director"]
    movie["director"] = ", ".join(directors) if directors else ""
    
    main_cast = [member["name"] for member in cast[:10]]
    movie["cast"] = ", ".join(main_cast) if main_cast else ""
    
    # Extract genres
    genres = data.get("genres", [])
    movie["genres"] = ", ".join([g.get("name", "") for g in genres])
    
    return movie

async def search_people(query: str, page: int = 1):
    url = f"{TMDB_BASE_URL}/3/search/person"
    params = {
        "query": query,
        "page": page,
        "include_adult": "false"
    }
    
    data = await fetch_with_retries(None, url, HEADERS, params)
    return {
        "page": data.get("page"),
        "total_results": data.get("total_results"),
        "total_pages": data.get("total_pages"),
        "results": data.get("results", [])
    }

TMDB_GENRES = {
    "Action": 28, "Adventure": 12, "Animation": 16, "Comedy": 35,
    "Crime": 80, "Documentary": 99, "Drama": 18, "Family": 10751,
    "Fantasy": 14, "History": 36, "Horror": 27, "Music": 10402,
    "Mystery": 9648, "Romance": 10749, "Science Fiction": 878,
    "TV Movie": 10770, "Thriller": 53, "War": 10752, "Western": 37
}

def sync_fetch(url, params):
    for attempt in range(3):
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=5.0, verify=False)
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == 2:
                return {}

def sync_get_person_id(name: str):
    if not name: return None
    url = f"{TMDB_BASE_URL}/3/search/person"
    params = {"query": name, "include_adult": "false", "page": 1}
    data = sync_fetch(url, params)
    results = data.get("results", [])
    if results:
        return results[0].get("id")
    return None

import concurrent.futures

def sync_discover_movies(params: dict, max_pages: int = 10):
    url = f"{TMDB_BASE_URL}/3/discover/movie"
    # force english text for our english model, sort by popularity
    p = {
        "language": "en-US",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "vote_count.gte": 10 # filter out spam
    }
    p.update(params)
    
    movies = []
    
    # Fetch page 1
    p1 = p.copy()
    p1["page"] = 1
    data1 = sync_fetch(url, p1)
    if not data1:
        return []
        
    movies.extend([format_movie(m) for m in data1.get("results", [])])
    
    total_pages = data1.get("total_pages", 1)
    fetch_pages = min(max_pages, total_pages)
    
    if fetch_pages > 1:
        def fetch_page(page_num):
            page_p = p.copy()
            page_p["page"] = page_num
            d = sync_fetch(url, page_p)
            return [format_movie(m) for m in d.get("results", [])] if d else []
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_page = {executor.submit(fetch_page, page): page for page in range(2, fetch_pages + 1)}
            for future in concurrent.futures.as_completed(future_to_page):
                try:
                    movies.extend(future.result())
                except Exception:
                    pass
                    
    return movies

