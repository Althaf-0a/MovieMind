import pandas as pd
import os

# Define the path to the master dataset
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MASTER_DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'movies_master.csv')

# Load the dataset globally when the application starts.
# This prevents reading from disk on every API request, which would be very slow for 45K rows.
print("Loading movies_master.csv into memory...")
movies_master_df = pd.read_csv(MASTER_DATA_PATH, low_memory=False)

# Ensure NaN values in text columns are treated as empty strings for safe searching
text_cols = ['title', 'original_title', 'overview_text', 'genres_text', 'cast_text', 'director_text', 'keywords_text']
for col in text_cols:
    if col in movies_master_df.columns:
        movies_master_df[col] = movies_master_df[col].fillna('')

print(f"Loaded {len(movies_master_df)} movies into the global data store.")

print("Loading movie_cast.csv and movie_directors.csv into memory...")
CAST_DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'movie_cast.csv')
DIRECTORS_DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'processed', 'movie_directors.csv')

movie_cast_df = pd.read_csv(CAST_DATA_PATH, low_memory=False)
movie_directors_df = pd.read_csv(DIRECTORS_DATA_PATH, low_memory=False)

movie_cast_df['actor_name'] = movie_cast_df['actor_name'].fillna('')
movie_directors_df['director_name'] = movie_directors_df['director_name'].fillna('')

print(f"Loaded {len(movie_cast_df)} cast relationships and {len(movie_directors_df)} director relationships.")
