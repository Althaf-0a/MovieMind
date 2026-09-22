import os
import math
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.data_store import movies_master_df

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, '..', 'data', 'processed')

EMBEDDINGS_PATH = os.path.join(PROCESSED_DATA_DIR, 'movie_embeddings.npy')
INDEX_PATH = os.path.join(PROCESSED_DATA_DIR, 'movie_embedding_index.csv')

# Global variables to cache the model and embeddings
semantic_model = None
movie_embeddings = None
embedding_index = None

def init_semantic_search():
    """Loads the model and embeddings into memory if they exist."""
    global semantic_model, movie_embeddings, embedding_index
    
    if semantic_model is not None:
        return # Already initialized
        
    print("Initializing Semantic Search engine...")
    if os.path.exists(EMBEDDINGS_PATH) and os.path.exists(INDEX_PATH):
        # 1. Load the model
        print("Loading sentence-transformer model...")
        semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 2. Load the embeddings and index
        print("Loading pre-computed embeddings...")
        movie_embeddings = np.load(EMBEDDINGS_PATH)
        embedding_index = pd.read_csv(INDEX_PATH)
        
        print(f"Semantic search initialized with {len(movie_embeddings)} movies.")
    else:
        print("Warning: Embedding files not found. Semantic search is disabled until built.")

def search_plot_semantic(query: str, limit: int = 10):
    global semantic_model, movie_embeddings, embedding_index
    
    # Lazy initialization
    if semantic_model is None:
        init_semantic_search()
        
    if semantic_model is None or movie_embeddings is None:
        # Fallback if embeddings are missing
        return []
        
    query = query.strip()
    if not query:
        return []
        
    # 1. Encode the query
    # encode() returns a numpy array, we reshape to (1, -1) for sklearn
    query_vector = semantic_model.encode([query])
    
    # 2. Calculate Cosine Similarity against all 44k movie embeddings
    # similarity_scores will have shape (1, N). Flatten it to 1D array.
    similarity_scores = cosine_similarity(query_vector, movie_embeddings).flatten()
    
    # 3. Get top matches
    # Filter out weak/negative matches (e.g. score <= 0.1)
    scores_with_indices = [(idx, score) for idx, score in enumerate(similarity_scores) if score > 0.1]
    
    # Sort descending
    sorted_scores = sorted(scores_with_indices, key=lambda x: x[1], reverse=True)[:limit]
    
    # 4. Map back to master dataset
    results = []
    
    # To quickly look up the row in movies_master_df by tmdbId, we can set an index, 
    # but for safety against modifying data_store's DF, we just filter.
    # A faster way:
    master_df_indexed = movies_master_df.set_index('tmdbId')
    
    for idx, score in sorted_scores:
        tmdb_id = embedding_index.iloc[idx]['tmdbId']
        
        if tmdb_id in master_df_indexed.index:
            row = master_df_indexed.loc[tmdb_id]
            
            results.append({
                "tmdbId": int(tmdb_id),
                "title": row['title'],
                "overview_text": row['overview_text'],
                "release_year": int(row['release_year']) if not math.isnan(row['release_year']) else None,
                "genres_text": row['genres_text'],
                "vote_average": float(row['vote_average']),
                "vote_count": int(row['vote_count']),
                "popularity": float(row['popularity']),
                "poster_path": row['poster_path'] if isinstance(row['poster_path'], str) else None,
                "similarity_score": round(float(score), 4)
            })
            
    return results
