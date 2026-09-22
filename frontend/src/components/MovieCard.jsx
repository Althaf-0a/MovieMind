import React from 'react';

const MovieCard = ({ movie, isPlotSearch, onClick }) => {
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

  const overview = movie.overview_text || movie.overview;
  const showOverview = isPlotSearch || movie._source === 'TMDB';

  return (
    <div 
      className={`movie-card ${movie._is_main ? 'main-movie' : ''}`} 
      onClick={() => onClick && onClick(movie)}
    >
      <div className="source-indicator">
        {movie._is_main ? 'MAIN MOVIE (TMDB)' : (movie._source || 'MovieMind Database')}
      </div>

      <div className="movie-poster">
        {posterUrl ? (
          <img src={posterUrl} alt={movie.title} />
        ) : (
          <span>No Poster</span>
        )}
      </div>

      <div className="movie-details-content">
        <h3>{movie.title} {releaseYear ? `(${releaseYear})` : ''}</h3>
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
        
        {(movie.similarity_score !== undefined || movie.match_score !== undefined || movie.final_score !== undefined) && (
          <div className="similarity">
            <strong>Match Score:</strong>{' '}
            {movie.final_score !== undefined
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
