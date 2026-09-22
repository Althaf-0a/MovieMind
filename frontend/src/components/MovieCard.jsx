import React from 'react';

// Reusable component to display a movie's details
const MovieCard = ({ movie, isPlotSearch, onClick }) => {
  // Handle genres which might be sent as a list string or actual array
  let genresText = '';
  if (typeof movie.genres_text === 'string') {
    genresText = movie.genres_text;
  } else if (typeof movie.genres === 'string') {
    // Fallback for older recommendation endpoint stringified array
    genresText = movie.genres.replace(/[\[\]']/g, '');
  } else if (Array.isArray(movie.genres)) {
    genresText = movie.genres.join(', ');
  }

  // Handle release year fallback
  let releaseYear = movie.release_year;
  if (!releaseYear && movie.release_date) {
    releaseYear = movie.release_date.split('-')[0];
  }

  // Handle poster URL
  let posterUrl = null;
  if (movie.poster_path) {
    posterUrl = movie.poster_path.startsWith('/') 
      ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
      : movie.poster_path;
  }

  // Handle overview
  const overview = movie.overview_text || movie.overview;
  
  // Show overview for plot search AND for TMDB fallback cards
  const showOverview = isPlotSearch || movie._source === 'TMDB';

  return (
    <div className={`movie-card ${movie._is_main ? 'main-movie' : ''}`} 
      onClick={() => onClick && onClick(movie)}
      style={{ 
      display: 'flex', gap: '15px', position: 'relative', 
      border: movie._is_main ? '2px solid #e50914' : 'none',
      padding: movie._is_main ? '15px' : '0',
      cursor: onClick ? 'pointer' : 'default'
    }}>
      
      <div className="source-indicator" style={{ position: 'absolute', top: '-10px', right: '-10px', background: '#e50914', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 'bold' }}>
        {movie._is_main ? 'MAIN MOVIE (TMDB)' : `Source: ${movie._source || 'MovieMind Database'}`}
      </div>

      <div className="movie-poster" style={{ flexShrink: 0, width: '100px', height: '150px', background: '#333', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px', overflow: 'hidden' }}>
        {posterUrl ? (
          <img src={posterUrl} alt={movie.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        ) : (
          <span style={{ color: '#888', fontSize: '0.8rem' }}>No Poster</span>
        )}
      </div>

      <div className="movie-details" style={{ flexGrow: 1 }}>
        <h3 style={{ margin: '0 0 10px 0' }}>{movie.title} {releaseYear ? `(${releaseYear})` : ''}</h3>
        <p style={{ margin: '0 0 10px 0' }}><strong>Genres:</strong> {genresText || 'Unknown'}</p>
        
        {showOverview && overview && (
          <p className="overview" style={{ margin: '0 0 10px 0', fontSize: '0.9rem', lineHeight: '1.4' }}>
            <strong>Plot:</strong> {overview.length > 200 ? `${overview.substring(0, 200)}...` : overview}
          </p>
        )}
        
        <div className="movie-stats" style={{ display: 'flex', gap: '15px', fontSize: '0.9rem', marginBottom: '10px' }}>
          <span><strong>Rating:</strong> {movie.vote_average ? Number(movie.vote_average).toFixed(1) : 'N/A'}/10 ({movie.vote_count || 0} votes)</span>
          <span><strong>Popularity:</strong> {movie.popularity ? Number(movie.popularity).toFixed(1) : '0'}</span>
        </div>
        
        {movie.relationship_reasons && movie.relationship_reasons.length > 0 && (
          <div className="relationship-reasons" style={{ fontSize: '0.9rem', color: '#ffb400', marginTop: '10px', fontStyle: 'italic' }}>
            <strong>Why it's related:</strong> {movie.relationship_reasons.join(', ')}
          </div>
        )}
        
        {movie.match_reasons && movie.match_reasons.length > 0 && (
          <div className="match-reasons" style={{ fontSize: '0.9rem', color: '#4caf50', marginTop: '10px' }}>
            <strong>Why this matches:</strong>
            <ul style={{ listStyleType: 'none', paddingLeft: '0', margin: '5px 0' }}>
              {movie.match_reasons.map((reason, idx) => (
                <li key={idx}>✓ {reason}</li>
              ))}
            </ul>
          </div>
        )}
        
        {(movie.similarity_score !== undefined || movie.match_score !== undefined || movie.final_score !== undefined) && (
          <div className="similarity" style={{ fontSize: '0.9rem', color: '#4caf50' }}>
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
