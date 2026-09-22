import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.services.data_store import movies_master_df

print("Building TF-IDF index for plot search (overview_text)...")
# Initialize the vectorizer with English stop words and a reasonable feature limit
plot_vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)

# We fit and transform the overview text ONCE when this module is imported.
# This prevents doing a massively expensive operation on every API request.
plot_tfidf_matrix = plot_vectorizer.fit_transform(movies_master_df['overview_text'])
print("Plot TF-IDF index built successfully.")

def search_by_plot(query: str, limit: int = 10):
    query = query.strip()
    if not query:
        return []
        
    # Transform the user's natural language query into a vector using our pre-fitted vectorizer
    query_vector = plot_vectorizer.transform([query])
    
    # Calculate cosine similarity between the query and all movie overviews
    similarity_scores = cosine_similarity(query_vector, plot_tfidf_matrix).flatten()
    
    # Enumerate scores with their index, and filter out movies with 0 similarity
    scores_with_indices = [(idx, score) for idx, score in enumerate(similarity_scores) if score > 0]
    
    # Sort descending by score
    sorted_scores = sorted(scores_with_indices, key=lambda x: x[1], reverse=True)[:limit]
    
    results = []
    for idx, score in sorted_scores:
        row = movies_master_df.iloc[idx]
        results.append({
            "tmdbId": int(row['tmdbId']),
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
