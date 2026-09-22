import math
from app.services.data_store import movies_master_df

def get_movies_catalog(
    page: int = 1, 
    limit: int = 50, 
    genre: str = None, 
    year: int = None, 
    min_rating: float = None, 
    min_votes: int = None, 
    sort_by: str = None
):
    df = movies_master_df
    
    # 1. Apply Filters
    if genre:
        df = df[df['genres_text'].str.lower().str.contains(genre.lower(), regex=False)]
        
    if year is not None:
        df = df[df['release_year'] == year]
        
    if min_rating is not None:
        df = df[df['vote_average'] >= min_rating]
        
    if min_votes is not None:
        df = df[df['vote_count'] >= min_votes]
        
    # 2. Apply Sorting
    valid_sorts = {
        'popularity': ('popularity', False),
        'vote_average': ('vote_average', False),
        'vote_count': ('vote_count', False),
        'release_year': ('release_year', False),
        'title': ('title', True) # Alphabetical ascending
    }
    
    if sort_by and sort_by in valid_sorts:
        col, ascending = valid_sorts[sort_by]
        df = df.sort_values(by=col, ascending=ascending)
    else:
        # Default sort by popularity if nothing specified
        df = df.sort_values(by='popularity', ascending=False)
        
    # 3. Pagination
    total_count = len(df)
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    paginated_df = df.iloc[start_idx:end_idx]
    
    results = []
    for _, row in paginated_df.iterrows():
        results.append({
            "tmdbId": int(row['tmdbId']),
            "title": row['title'],
            "release_year": int(row['release_year']) if not math.isnan(row['release_year']) else None,
            "genres_text": row['genres_text'],
            "vote_average": float(row['vote_average']),
            "vote_count": int(row['vote_count']),
            "popularity": float(row['popularity']),
            "poster_path": row['poster_path'] if isinstance(row['poster_path'], str) else None
        })
        
    return {
        "total_results": total_count,
        "page": page,
        "limit": limit,
        "results": results
    }
