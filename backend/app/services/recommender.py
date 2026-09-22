import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'movies_processed.csv')

# --- 1. Load Data ---
# Load the processed movies dataset
movies_df = pd.read_csv(DATA_PATH)

# Handle any potentially missing tags safely by filling with empty strings
movies_df['tags'] = movies_df['tags'].fillna('')

# --- 2. TF-IDF Vectorization ---
# What is TF-IDF?
# Term Frequency-Inverse Document Frequency (TF-IDF) is a statistical measure that evaluates 
# how relevant a word is to a document in a collection of documents. 
# It rewards words that appear frequently in a specific movie's tags (TF) but 
# penalizes words that appear too frequently across ALL movies (IDF) like "the", "and", etc.

# We configure the vectorizer with:
# - stop_words='english': removes common English words that don't add semantic value.
# - max_features=5000: limits the vocabulary to the top 5000 most frequent unique words. 
#   This reduces memory usage and prevents rare words from dominating the similarity scores.
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)

# Fit the vectorizer on the tags and generate the TF-IDF matrix
# What is the TF-IDF matrix?
# It's a 2D matrix where each row represents a movie, and each column represents a unique word from our 5000 vocabulary.
# The values are the TF-IDF weights.
tfidf_matrix = vectorizer.fit_transform(movies_df['tags'])

# --- 3. Cosine Similarity ---
# What is Cosine Similarity?
# It calculates the cosine of the angle between two vectors (in this case, two movies in the TF-IDF matrix).
# A score of 1 means the vectors point in the exact same direction (identical tags).
# A score of 0 means they are completely orthogonal (no shared words).
similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

def recommend_movies(movie_title: str, top_n: int = 10):
    """
    Given a movie title, recommends top_n similar movies using cosine similarity of their tags.
    """
    # 1. Handle case insensitivity and find the movie index
    idx = movies_df[movies_df['title'].str.lower() == movie_title.lower()].index
    
    # Handle cases where the requested movie does not exist
    if len(idx) == 0:
        return {"error": f"Movie '{movie_title}' not found in the dataset."}
    
    # Handle duplicate movie titles (take the first match)
    movie_index = idx[0]
    
    # 2. Get similarity scores for all movies compared to the selected movie
    # similarity_matrix[movie_index] gives an array of similarity scores against all other movies
    similarity_scores = list(enumerate(similarity_matrix[movie_index]))
    
    # 3. Sort the movies based on the similarity scores in descending order
    # x[1] is the similarity score
    sorted_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    
    # 4. Extract the top N similar movies
    # We start from index 1 to exclude the selected movie itself (which will always be index 0 with a score of 1.0)
    top_movies = sorted_scores[1:top_n+1]
    
    # 5. Format the results
    recommendations = []
    
    # Let's optionally join with movies_master to get posters
    try:
        from app.services.data_store import movies_master_df
        master_dict = movies_master_df.set_index('tmdbId')['poster_path'].to_dict()
    except Exception:
        master_dict = {}
        
    for i, score in top_movies:
        row = movies_df.iloc[i]
        tmdb_id = int(row['id'])
        poster = master_dict.get(tmdb_id)
        if type(poster) != str:
            poster = None
            
        recommendations.append({
            "id": tmdb_id,
            "title": row['title'],
            "genres": row['genres'],
            "vote_average": float(row['vote_average']),
            "vote_count": int(row['vote_count']),
            "popularity": float(row['popularity']),
            "poster_path": poster,
            "similarity_score": round(float(score), 4)
        })
        
    return recommendations


if __name__ == "__main__":
    # --- TEST SCRIPT ---
    print(f"Number of movies used: {movies_df.shape[0]}")
    print(f"Number of TF-IDF features: {tfidf_matrix.shape[1]}")
    print(f"Shape of the TF-IDF matrix: {tfidf_matrix.shape}")
    
    print("\n--- Test 1: Valid Movie Title ('Avatar') ---")
    recs = recommend_movies("Avatar", top_n=5)
    for r in recs:
        print(f"Title: {r['title']}, Sim Score: {r['similarity_score']}")
        
    print("\n--- Test 2: Valid Movie Title ('The Dark Knight') ---")
    recs2 = recommend_movies("The Dark Knight", top_n=3)
    for r in recs2:
        print(f"Title: {r['title']}, Sim Score: {r['similarity_score']}")
        
    print("\n--- Test 3: Invalid Movie Title ---")
    print(recommend_movies("Unknown Movie 123", top_n=5))
