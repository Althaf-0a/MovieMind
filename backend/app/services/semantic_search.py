import os
import math
import numpy as np
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.data_store import movies_master_df

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, '..', 'data', 'processed')

EMBEDDINGS_PATH = os.path.join(PROCESSED_DATA_DIR, 'movie_embeddings_finetuned.npy')
INDEX_PATH = os.path.join(PROCESSED_DATA_DIR, 'movie_embedding_index_finetuned.csv')
FAISS_PATH = os.path.join(PROCESSED_DATA_DIR, 'movie_embeddings_finetuned.faiss')

# Global variables to cache the model and embeddings
semantic_model = None
movie_embeddings = None
embedding_index = None
faiss_index = None

def init_semantic_search():
    """Loads the model, embeddings, and FAISS index into memory if they exist."""
    global semantic_model, movie_embeddings, embedding_index, faiss_index
    
    if semantic_model is not None:
        return # Already initialized
        
    print("Initializing Semantic Search engine...")
    if os.path.exists(EMBEDDINGS_PATH) and os.path.exists(INDEX_PATH) and os.path.exists(FAISS_PATH):
        # 1. Load the model
        print("Loading fine-tuned sentence-transformer model...")
        model_dir = os.path.join(BASE_DIR, '..', 'models', 'movie_plot_minilm_finetuned')
        semantic_model = SentenceTransformer(model_dir)
        
        # 2. Load the embeddings and index
        print("Loading pre-computed embeddings and FAISS index...")
        movie_embeddings = np.load(EMBEDDINGS_PATH)
        embedding_index = pd.read_csv(INDEX_PATH)
        faiss_index = faiss.read_index(FAISS_PATH)
        
        print(f"Semantic search initialized with {faiss_index.ntotal} movies in FAISS.")
    else:
        print("Warning: Embedding or FAISS files not found. Semantic search is disabled until built.")

def search_faiss(query_vector, top_k=500):
    """Reusable FAISS search function."""
    global faiss_index
    if faiss_index is None:
        return []
    
    # Ensure vector is float32 and shape (1, dim)
    q = np.array(query_vector, dtype=np.float32)
    if len(q.shape) == 1:
        q = q.reshape(1, -1)
        
    faiss.normalize_L2(q)
    
    k = min(top_k, faiss_index.ntotal)
    distances, indices = faiss_index.search(q, k)
    
    results = []
    for i in range(k):
        idx = int(indices[0][i])
        score = float(distances[0][i])
        if idx != -1:
            results.append((idx, score))
            
    return results

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
    
    # 2. FAISS Nearest Neighbor Search
    scores_with_indices = search_faiss(query_vector, top_k=limit * 10)
    
    # 3. Get top matches (filter weak matches and take limit)
    scores_with_indices = [x for x in scores_with_indices if x[1] > 0.1][:limit]
    
    # 4. Map back to master dataset
    results = []
    
    # To quickly look up the row in movies_master_df by tmdbId, we can set an index, 
    # but for safety against modifying data_store's DF, we just filter.
    # A faster way:
    master_df_indexed = movies_master_df.set_index('tmdbId')
    
    for idx, score in scores_with_indices:
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

def search_similar_by_tmdb_id(tmdb_id: int, min_year: int = None, max_year: int = None, limit: int = 10):
    global semantic_model, movie_embeddings, embedding_index
    
    if semantic_model is None:
        init_semantic_search()
        
    if semantic_model is None or movie_embeddings is None:
        return []
        
    # Find the row index of the given tmdb_id in the embedding matrix
    matching_indices = embedding_index[embedding_index['tmdbId'] == tmdb_id].index.tolist()
    if not matching_indices:
        return [] # Movie not found in embeddings
        
    source_idx = matching_indices[0]
    source_vector = movie_embeddings[source_idx].reshape(1, -1)
    
    # 2. FAISS Nearest Neighbor Search
    # Fetch extra candidates since we'll filter out the source movie and by year
    scores_with_indices = search_faiss(source_vector, top_k=limit * 10 + 50)
    
    # Filter weak matches
    sorted_scores = [x for x in scores_with_indices if x[1] > 0.1]
    
    master_df_indexed = movies_master_df.set_index('tmdbId')
    
    results = []
    for idx, score in sorted_scores:
        if len(results) >= limit:
            break
            
        current_tmdb_id = embedding_index.iloc[idx]['tmdbId']
        
        # Exclude the source movie itself
        if current_tmdb_id == tmdb_id:
            continue
            
        if current_tmdb_id in master_df_indexed.index:
            row = master_df_indexed.loc[current_tmdb_id]
            rel_year = int(row['release_year']) if not math.isnan(row['release_year']) else None
            
            # Apply year filters
            if min_year is not None and (rel_year is None or rel_year < min_year):
                continue
            if max_year is not None and (rel_year is None or rel_year > max_year):
                continue
            
            results.append({
                "tmdbId": int(current_tmdb_id),
                "title": row['title'],
                "overview_text": row['overview_text'] if 'overview_text' in row else '',
                "release_year": rel_year,
                "genres_text": row['genres_text'],
                "vote_average": float(row['vote_average']),
                "vote_count": int(row['vote_count']),
                "popularity": float(row['popularity']),
                "poster_path": row['poster_path'] if isinstance(row['poster_path'], str) else None,
                "similarity_score": round(float(score), 4),
                "match_score": round(float(score) * 100, 2), # Scale 0-100 for UI
                "resolved_title": f"Semantically similar to: {master_df_indexed.loc[tmdb_id]['title']}"
            })
            
    return results

def score_external_texts(query_vector, texts: list):
    """
    Dynamically embeds a list of external texts, L2 normalizes them exactly like the FAISS index,
    and returns a list of cosine similarity scores against the provided query vector.
    """
    if not texts:
        return []
    
    text_vectors = semantic_model.encode(texts)
    text_vectors = np.array(text_vectors, dtype=np.float32)
    if len(text_vectors.shape) == 1:
        text_vectors = text_vectors.reshape(1, -1)
    
    faiss.normalize_L2(text_vectors)
    
    # Query vector is already L2 normalized in search_faiss, or earlier
    # wait, query_vector passed here might not be normalized yet if caller didn't normalize it!
    # Let's make sure it is normalized
    query_vector_copy = np.copy(query_vector).astype(np.float32)
    if len(query_vector_copy.shape) == 1:
        query_vector_copy = query_vector_copy.reshape(1, -1)
    faiss.normalize_L2(query_vector_copy)
    
    # Compute dot product (Cosine Similarity since both are L2 normalized)
    scores = np.dot(text_vectors, query_vector_copy.T).flatten()
    return scores.tolist()

