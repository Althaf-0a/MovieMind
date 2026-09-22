import re
from rapidfuzz import process, fuzz
import pandas as pd
from app.services.data_store import movie_cast_df, movie_directors_df, movies_master_df

_UNIQUE_ACTORS = []
_UNIQUE_DIRECTORS = []
_UNIQUE_TITLES = []

# Dictionaries mapping normalized text to their canonical forms
_NORM_ACTORS_MAP = {}
_NORM_DIRECTORS_MAP = {}
_NORM_TITLES_MAP = {}

def normalize_text(text: str) -> str:
    """Lowercase, strip, collapse spaces, remove basic punctuation."""
    if not text or not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return " ".join(text.split())

def init_resolver():
    global _UNIQUE_ACTORS, _UNIQUE_DIRECTORS, _UNIQUE_TITLES
    global _NORM_ACTORS_MAP, _NORM_DIRECTORS_MAP, _NORM_TITLES_MAP
    
    if not _UNIQUE_ACTORS:
        _UNIQUE_ACTORS = movie_cast_df['actor_name'].dropna().unique().tolist()
        for name in _UNIQUE_ACTORS:
            norm = normalize_text(name)
            # Store the first canonical mapping we find
            if norm and norm not in _NORM_ACTORS_MAP:
                _NORM_ACTORS_MAP[norm] = name
                
    if not _UNIQUE_DIRECTORS:
        _UNIQUE_DIRECTORS = movie_directors_df['director_name'].dropna().unique().tolist()
        for name in _UNIQUE_DIRECTORS:
            norm = normalize_text(name)
            if norm and norm not in _NORM_DIRECTORS_MAP:
                _NORM_DIRECTORS_MAP[norm] = name
                
    if not _UNIQUE_TITLES:
        _UNIQUE_TITLES = movies_master_df['title'].dropna().unique().tolist()
        for title in _UNIQUE_TITLES:
            norm = normalize_text(title)
            if norm and norm not in _NORM_TITLES_MAP:
                _NORM_TITLES_MAP[norm] = title

def custom_scorer(s1, s2, **kwargs):
    """
    Score using a mix of QRatio (exact match with typos) and token_sort_ratio (out of order words).
    Returns the maximum of the two to be resilient.
    """
    q_score = fuzz.QRatio(s1, s2, **kwargs)
    t_score = fuzz.token_sort_ratio(s1, s2, **kwargs)
    return max(q_score, t_score)

def _resolve_generic(query: str, norm_map: dict, threshold: float = 85.0):
    if not query:
        return {"input": query, "resolved": None, "score": 0.0, "matched": False}
        
    query_norm = normalize_text(query)
    if not query_norm:
        return {"input": query, "resolved": None, "score": 0.0, "matched": False}
        
    # 1. Exact match on normalized form
    if query_norm in norm_map:
        return {
            "input": query,
            "resolved": norm_map[query_norm],
            "score": 100.0,
            "matched": True,
            "ambiguous": False,
            "suggestions": []
        }
        
    # 2. Fuzzy match against the normalized keys
    candidates_norm = list(norm_map.keys())
    
    matches = process.extract(
        query_norm,
        candidates_norm,
        scorer=custom_scorer,
        limit=5
    )
    
    if not matches:
        return {"input": query, "resolved": None, "score": 0.0, "matched": False}
        
    best_match_norm, best_score, _ = matches[0]
    
    if best_score >= threshold:
        ambiguous = False
        suggestions = []
        
        # Check for ambiguity
        if len(matches) > 1:
            second_match_norm, second_score, _ = matches[1]
            if (best_score - second_score < 2.0) and (best_score < 100.0):
                ambiguous = True
                suggestions = [norm_map[m[0]] for m in matches if m[1] >= best_score - 2.0]
                
        return {
            "input": query,
            "resolved": norm_map[best_match_norm],
            "score": round(best_score, 2),
            "matched": True,
            "ambiguous": ambiguous,
            "suggestions": suggestions if ambiguous else []
        }
        
    return {
        "input": query,
        "resolved": None,
        "score": round(best_score, 2),
        "matched": False,
        "ambiguous": False,
        "suggestions": [norm_map[m[0]] for m in matches if m[1] > max(60.0, best_score - 10.0)]
    }

def resolve_actor(query: str) -> dict:
    init_resolver()
    return _resolve_generic(query, _NORM_ACTORS_MAP, threshold=85.0)
    
def resolve_director(query: str) -> dict:
    init_resolver()
    return _resolve_generic(query, _NORM_DIRECTORS_MAP, threshold=85.0)
    
def resolve_title(query: str) -> dict:
    init_resolver()
    # High threshold for titles to avoid "Spider-Man No Way Home" -> "Spider-Man"
    return _resolve_generic(query, _NORM_TITLES_MAP, threshold=90.0)
