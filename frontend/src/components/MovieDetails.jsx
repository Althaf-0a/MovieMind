import React, { useState, useEffect } from 'react';
import { getLocalMovieDetails, getRecommendations as getLocalRecommendations, getTmdbMovieDetails, getRelatedMovies as getTmdbRelatedMovies } from '../services/api';
import MovieCard from './MovieCard';

const MovieDetails = ({ movie, onBack }) => {
  const [details, setDetails] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDetails = async () => {
      setLoading(true);
      setError(null);
      window.scrollTo(0, 0);
      try {
        const isTmdb = movie._source === 'TMDB';
        const movieId = movie.id || movie.tmdbId;
        
        let fetchedDetails;
        let fetchedSimilar = [];
        
        if (isTmdb) {
          fetchedDetails = await getTmdbMovieDetails(movieId);
          const related = await getTmdbRelatedMovies(movieId);
          fetchedSimilar = related.related_movies || [];
        } else {
          fetchedDetails = await getLocalMovieDetails(movieId);
          try {
            const recs = await getLocalRecommendations(fetchedDetails.title || movie.title, 10);
            fetchedSimilar = recs.recommendations || [];
          } catch (e) {
            console.error("Could not fetch local recommendations:", e);
          }
        }
        
        setDetails(fetchedDetails);
        setSimilar(fetchedSimilar);
      } catch (err) {
        console.error(err);
        setError("Failed to load movie details.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchDetails();
  }, [movie]);

  if (loading) {
    return (
      <div className="state-message loading">
        <div className="spinner-large"></div>
        <p>Loading movie details...</p>
      </div>
    );
  }

  if (error || !details) {
    return (
      <div className="movie-details-view">
        <button className="btn-back" onClick={onBack}>&larr; Back to Results</button>
        <div className="state-message error">
          <div className="icon">⚠️</div>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const title = details.title || details.original_title;
  let releaseYear = details.release_year;
  if (!releaseYear && details.release_date) releaseYear = details.release_date.split('-')[0];
  
  const posterUrl = details.poster_path ? 
    (details.poster_path.startsWith('/') ? `https://image.tmdb.org/t/p/w500${details.poster_path}` : details.poster_path) 
    : null;
    
  let genresText = '';
  if (typeof details.genres_text === 'string') genresText = details.genres_text;
  else if (typeof details.genres === 'string') genresText = details.genres;
  else if (Array.isArray(details.genres)) genresText = details.genres.join(', ');

  const rating = details.vote_average ? Number(details.vote_average).toFixed(1) : 'N/A';
  const votes = details.vote_count || 0;
  const overview = details.overview_text || details.overview || "No overview available.";
  const director = details.director_text || details.director || "Unknown";
  const cast = details.cast_text || details.cast || "Unknown";

  return (
    <div className="movie-details-view">
      <button className="btn-back" onClick={onBack}>&larr; Back to Results</button>
      
      <div className="details-header">
        <div className="details-poster">
          {posterUrl ? (
            <img src={posterUrl} alt={title} />
          ) : (
            <div className="no-poster">No Poster</div>
          )}
        </div>
        
        <div className="details-info">
          <h1>{title} {releaseYear ? `(${releaseYear})` : ''}</h1>
          <div className={`source-badge ${movie._source === 'TMDB' ? 'tmdb-badge' : 'local-badge'}`}>
            Source: {movie._source || 'MovieMind Database'}
          </div>
          
          <div className="rating-block">
            <span><strong>&#9733; {rating}</strong>/10 ({votes} votes)</span>
          </div>
          
          <p><strong>Genres:</strong> {genresText}</p>
          <p><strong>Director:</strong> {director}</p>
          <p><strong>Main Cast:</strong> {cast}</p>
          
          <div className="details-overview">
            <h3>Overview</h3>
            <p>{overview}</p>
          </div>
        </div>
      </div>
      
      {similar.length > 0 && (
        <div className="similar-movies">
          <h2>Similar Movies</h2>
          <div className="movie-list">
            {similar.map((simMovie, idx) => {
              const mappedMovie = {
                ...simMovie,
                _source: movie._source
              };
              return <MovieCard key={simMovie.id || simMovie.tmdbId || idx} movie={mappedMovie} isPlotSearch={false} />;
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default MovieDetails;
