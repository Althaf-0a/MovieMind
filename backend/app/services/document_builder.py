import pandas as pd

def build_semantic_document(row: pd.Series) -> str:
    """
    Constructs the semantic document representing a movie for embedding generation.
    Combines Title, Overview, Genres, and Keywords to provide a richer semantic signal.
    """
    title = str(row['title']) if 'title' in row and not pd.isna(row['title']) else ""
    overview = str(row['overview_text']) if 'overview_text' in row and not pd.isna(row['overview_text']) else ""
    genres = str(row['genres_text']) if 'genres_text' in row and not pd.isna(row['genres_text']) else ""
    keywords = str(row['keywords_text']) if 'keywords_text' in row and not pd.isna(row['keywords_text']) else ""
    
    parts = []
    
    if title:
        parts.append(f"Title: {title}")
        
    if overview:
        parts.append(f"Overview: {overview}")
        
    if genres:
        parts.append(f"Genres: {genres}")
        
    if keywords:
        parts.append(f"Keywords: {keywords}")
        
    # Join with newlines to keep it structured, but the embedding model will treat it as one continuous document.
    return "\n".join(parts)
