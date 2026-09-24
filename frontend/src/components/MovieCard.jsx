import React from 'react';

import { useState } from "react";

const MovieCard = ({ movie, isPlotSearch, onClick, isSaved, onToggleWatchlist, isWatchlistView }) => {
  const [isToggling, setIsToggling] = useState(false);
  let genresText = '';
  if (typeof movie.genres_text === 'string') {
    genresText = movie.genres_text;
  } else if (typeof movie.genres === 'string') {
    genresText = movie.genres.replace(/[\[\]']/g, '');
  } else if (Array.isArray(movie.genres)) {
    genresText = movie.genres.join(', ');
  }

  let releaseYear = movie.release_year;
  if (!releaseYear && movie.release_date) {
    releaseYear = movie.release_date.split('-')[0];
  }

  let posterUrl = null;
  if (movie.poster_path) {
    posterUrl = movie.poster_path.startsWith('/') 
      ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
      : movie.poster_path;
  }

  

  const handleToggle = async (e) => {
    e.stopPropagation();
    if (isToggling) return;
    setIsToggling(true);
    try {
      if (onToggleWatchlist) {
        await onToggleWatchlist(movie);
      }
    } catch (err) {
      console.error("Failed to toggle watchlist", err);
    } finally {
      setIsToggling(false);
    }
  };

  const overview = movie.overview_text || movie.overview;
  const showOverview = isPlotSearch || movie._source === 'TMDB';

  const fallbackImage = '/placeholder.svg';

  const handleImageError = (e) => {
    if (e.target.src !== window.location.origin + fallbackImage) {
      e.target.onerror = null;
      e.target.src = fallbackImage;
    }
  };

  return (
    <div 
      className={`movie-card ${movie._is_main ? 'main-movie' : ''}`} 
      onClick={() => onClick && onClick(movie)}
    >
      <div className="movie-poster">
        {posterUrl ? (
          <img src={posterUrl} alt={movie.title} onError={handleImageError} />
        ) : (
          <img src={fallbackImage} alt="No Poster Available" />
        )}
      </div>

      <div className="movie-details-content">
        <div className="movie-header" style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '10px' }}>
          <div className="movie-title-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px' }}>
            <h3 style={{ margin: 0, minWidth: 0, flex: 1, overflowWrap: 'anywhere' }}>{movie.title} {releaseYear ? `(${releaseYear})` : ''}</h3>
            <span className="source-indicator-inline" style={{ fontSize: '0.75rem', padding: '4px 8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', whiteSpace: 'nowrap' }}>
              {movie._is_main ? 'TMDB MAIN' : (movie._source || 'Local DB')}
            </span>
          </div>
          <button 
            className={`watchlist-boxed-btn ${isSaved ? 'saved' : ''}`}
            onClick={handleToggle}
            disabled={isToggling}
            style={{ alignSelf: 'flex-start' }}
          >
            {isToggling ? '...' : (isWatchlistView && isSaved ? '\u2665 Remove from Watchlist' : (isSaved ? '\u2665 Saved' : '\u2661 Save to Watchlist'))}
          </button>
        </div>
        <p><strong>Genres:</strong> {genresText || 'Unknown'}</p>
        
        {showOverview && overview && (
          <p className="overview">
            <strong>Plot:</strong> {overview.length > 200 ? `${overview.substring(0, 200)}...` : overview}
          </p>
        )}
        
        <div className="movie-stats">
          <span><strong>Rating:</strong> {movie.vote_average ? Number(movie.vote_average).toFixed(1) : 'N/A'}/10 ({movie.vote_count || 0} votes)</span>
          <span><strong>Popularity:</strong> {movie.popularity ? Number(movie.popularity).toFixed(1) : '0'}</span>
        </div>
        
        {movie.relationship_reasons && movie.relationship_reasons.length > 0 && (
          <div className="match-reasons" style={{ borderColor: '#f59e0b', background: 'rgba(245, 158, 11, 0.1)' }}>
            <strong style={{ color: '#f59e0b' }}>Why it's related:</strong> {movie.relationship_reasons.join(', ')}
          </div>
        )}
        
        {movie.match_reasons && movie.match_reasons.length > 0 && (
          <div className="match-reasons">
            <strong>Match Reasons:</strong>
            <ul>
              {movie.match_reasons.map((reason, idx) => (
                <li key={idx}>✓ {reason}</li>
              ))}
            </ul>
          </div>
        )}
        
        {(movie.related_to_title || movie.similarity_score !== undefined || movie.match_score !== undefined || movie.final_score !== undefined) && (
          <div className="similarity">
            {movie.related_to_title && (
              <div style={{ marginBottom: '4px' }}>
                <strong>Related to:</strong> {movie.related_to_title}
              </div>
            )}
            <strong>Match Score:</strong>{' '}
            {movie.related_to_score !== undefined
              ? `${Number(movie.related_to_score).toFixed(1)}%`
              : movie.final_score !== undefined
                ? `${Number(movie.final_score).toFixed(1)}%`
                : movie.match_score !== undefined 
                  ? `${Number(movie.match_score).toFixed(1)}%` 
                  : `${(Number(movie.similarity_score) * 100).toFixed(1)}%`}
          </div>
        )}
      </div>
    </div>
  );
};

export default MovieCard;

