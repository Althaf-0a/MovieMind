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
      window.scrollTo(0, 0); // Scroll to top when loading new details
      try {
        const isTmdb = movie._source === 'TMDB';
        const movieId = movie.id || movie.tmdbId; // Just in case
        
        let fetchedDetails;
        let fetchedSimilar = [];
        
        if (isTmdb) {
          fetchedDetails = await getTmdbMovieDetails(movieId);
          const related = await getTmdbRelatedMovies(movieId);
          fetchedSimilar = related.related_movies || [];
        } else {
          fetchedDetails = await getLocalMovieDetails(movieId);
          // Local similar requires the title
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
    return <div className="loading">Loading movie details...</div>;
  }

  if (error || !details) {
    return (
      <div>
        <button onClick={onBack} style={{ marginBottom: '20px' }}>&larr; Back to Results</button>
        <div className="error-message">{error}</div>
      </div>
    );
  }

  // Formatting for display
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
      <button onClick={onBack} style={{ marginBottom: '20px', padding: '8px 16px', cursor: 'pointer', background: '#333', color: 'white', border: 'none', borderRadius: '4px' }}>
        &larr; Back to Results
      </button>
      
      <div className="details-header" style={{ display: 'flex', gap: '30px', marginBottom: '40px' }}>
        <div className="details-poster" style={{ flexShrink: 0, width: '300px', borderRadius: '8px', overflow: 'hidden', background: '#222' }}>
          {posterUrl ? (
            <img src={posterUrl} alt={title} style={{ width: '100%', display: 'block' }} />
          ) : (
            <div style={{ padding: '40px', textAlign: 'center', color: '#888' }}>No Poster</div>
          )}
        </div>
        
        <div className="details-info" style={{ flexGrow: 1 }}>
          <h1 style={{ margin: '0 0 10px 0', fontSize: '2.5rem' }}>{title} {releaseYear ? `(${releaseYear})` : ''}</h1>
          <div className="source-badge" style={{ display: 'inline-block', background: movie._source === 'TMDB' ? '#01b4e4' : '#e50914', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 'bold', marginBottom: '20px' }}>
            Source: {movie._source || 'MovieMind Database'}
          </div>
          
          <div style={{ display: 'flex', gap: '20px', marginBottom: '20px', fontSize: '1.1rem' }}>
            <span><strong>&#9733; {rating}</strong>/10 ({votes} votes)</span>
          </div>
          
          <p style={{ fontSize: '1.1rem', marginBottom: '10px' }}><strong>Genres:</strong> {genresText}</p>
          <p style={{ fontSize: '1.1rem', marginBottom: '10px' }}><strong>Director:</strong> {director}</p>
          <p style={{ fontSize: '1.1rem', marginBottom: '20px' }}><strong>Main Cast:</strong> {cast}</p>
          
          <div className="details-overview">
            <h3 style={{ margin: '0 0 10px 0' }}>Overview</h3>
            <p style={{ lineHeight: '1.6', fontSize: '1.1rem' }}>{overview}</p>
          </div>
        </div>
      </div>
      
      {similar.length > 0 && (
        <div className="similar-movies">
          <h2 style={{ borderBottom: '1px solid #444', paddingBottom: '10px', marginBottom: '20px' }}>Similar Movies</h2>
          <div className="results-list" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {similar.map((simMovie, idx) => {
              // Ensure we pass a movie object that MovieCard understands
              const mappedMovie = {
                ...simMovie,
                _source: movie._source // Keep source consistent for recommendations
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
