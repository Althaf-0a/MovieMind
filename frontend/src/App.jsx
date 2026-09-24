import React, { useState } from 'react'
import './App.css'
import { 
  searchHybridDiscovery, 
  searchMovies, 
  searchTMDBMovies, 
  searchPeople,
  getRelatedMovies
} from './services/api'
import MovieCard from './components/MovieCard'
import MovieDetails from './components/MovieDetails'
import AuthModal from './components/AuthModal'
import { getCurrentUser, getWatchlist, addToWatchlist, removeFromWatchlist, getSuggestedMovies } from './services/api'
import { useEffect } from 'react'


const MODES = {
  STORY: 'STORY',
  TITLE: 'TITLE',
  ACTOR: 'ACTOR',
  DIRECTOR: 'DIRECTOR',
  WATCHLIST: 'WATCHLIST',
  SUGGESTED: 'SUGGESTED',
}

function App() {
  const [currentMode, setCurrentMode] = useState(MODES.STORY)
  const [query, setQuery] = useState('')
  const [actor, setActor] = useState('')
  const [director, setDirector] = useState('')
  const [genre, setGenre] = useState('')
  const [minYear, setMinYear] = useState('')
  const [maxYear, setMaxYear] = useState('')
  const [minRating, setMinRating] = useState('')
  const [limit, setLimit] = useState(10)
  
  const [showAdvanced, setShowAdvanced] = useState(false)
  
  const [results, setResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const [requestedQuery, setRequestedQuery] = useState('')
  const [resolvedTitleContext, setResolvedTitleContext] = useState(null)
  const [selectedMovie, setSelectedMovie] = useState(null)

  const [currentUser, setCurrentUser] = useState(null)
  const [watchlist, setWatchlist] = useState(new Set())
  const [watchlistMovies, setWatchlistMovies] = useState([])
  const [suggestedMovies, setSuggestedMovies] = useState([])
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [isAuthLoading, setIsAuthLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      if (localStorage.getItem('moviemind_token')) {
        sessionStorage.removeItem('moviemind_token')
      }
      const token = sessionStorage.getItem('moviemind_token')
      if (token) {
        try {
          const user = await getCurrentUser()
          setCurrentUser(user)
          
          try {
            const savedItems = await getWatchlist()
            const tmdbIds = new Set(savedItems.map(item => item.tmdb_id))
            setWatchlist(tmdbIds)
          } catch (watchErr) {
            console.error("Failed to fetch watchlist:", watchErr)
          }
          
        } catch (err) {
          sessionStorage.removeItem('moviemind_token')
          setCurrentUser(null)
        }
      }
      setIsAuthLoading(false)
    }
    initAuth()
  }, [])

  const handleLogout = () => {
    sessionStorage.removeItem('moviemind_token')
    setCurrentUser(null)
    setWatchlist(new Set())
    setCurrentMode(MODES.STORY)
  }


const handleToggleWatchlist = async (movie) => {
    if (!currentUser) {
      setShowAuthModal('login')
      return
    }
    
    const tmdbId = movie.id || movie.tmdbId
    const isSaved = watchlist.has(tmdbId)
    
    try {
      if (isSaved) {
        await removeFromWatchlist(tmdbId)
        setWatchlist(prev => {
          const next = new Set(prev)
          next.delete(tmdbId)
          return next
        })
      } else {
        const payload = {
          tmdb_id: tmdbId,
          title: movie.title || movie.original_title,
          release_year: movie.release_year || (movie.release_date ? parseInt(movie.release_date.split('-')[0]) : null),
          poster_path: movie.poster_path,
          source: movie.source || (movie._source === 'TMDB' ? 'tmdb' : 'local')
        }
        await addToWatchlist(payload)
        setWatchlist(prev => {
          const next = new Set(prev)
          next.add(tmdbId)
          return next
        })
      }
    } catch (err) {
      console.error("Error toggling watchlist:", err)
      alert("Failed to update watchlist. Please try again.")
    }
  }

  const handleModeChange = async (mode) => {
    setCurrentMode(mode)
    setError(null)
    setSelectedMovie(null)
    
    if (mode === MODES.WATCHLIST) {
      if (!currentUser) return
      setIsLoading(true)
      try {
        const items = await getWatchlist()
        setWatchlistMovies(items.map(item => ({
          id: item.tmdb_id,
          tmdbId: item.tmdb_id,
          title: item.title,
          release_year: item.release_year,
          poster_path: item.poster_path,
          _source: item.source || 'Local DB'
        })))
      } catch (err) {
        console.error(err)
        setError("Failed to load watchlist.")
      } finally {
        setIsLoading(false)
      }
    } else if (mode === MODES.SUGGESTED) {
      if (!currentUser) return
      setIsLoading(true)
      try {
        
        const items = await getSuggestedMovies()
        setSuggestedMovies(items)
      } catch (err) {
        console.error(err)
        setError("Failed to load suggested movies: " + (err.message || err.toString()))
      } finally {
        setIsLoading(false)
      }
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim() && currentMode !== MODES.STORY && !actor.trim() && !director.trim()) return

    const parsedMinYear = minYear ? parseInt(minYear) : null
    const parsedMaxYear = maxYear ? parseInt(maxYear) : null

    if (parsedMinYear !== null && parsedMaxYear !== null && parsedMinYear > parsedMaxYear) {
      setError("Validation Error: 'From Year' cannot be greater than 'To Year'.")
      setResults([])
      return
    }

    setIsLoading(true)
    setError(null)
    setResults([])
    setRequestedQuery(query)
      setResolvedTitleContext(null)
    setSelectedMovie(null)

    try {
      let data = []
      if (currentMode === MODES.STORY) {
        const response = await searchHybridDiscovery({
          plot: query,
          actor: actor,
          director: director,
          genre: genre,
          min_year: parsedMinYear,
          max_year: parsedMaxYear,
          min_rating: minRating ? parseFloat(minRating) : null,
          top_n: limit
        })
        data = (response.results || []).map(m => ({ ...m, _source: 'MovieMind Database' }))
      } else if (currentMode === MODES.TITLE) {
        const titleSearchResponse = await searchMovies(query, parsedMinYear, parsedMaxYear, limit)
        
        if (titleSearchResponse && titleSearchResponse.resolved_movie) {
          setResolvedTitleContext(titleSearchResponse.resolved_movie)
        }
        
        data = (titleSearchResponse.results || []).map(m => ({ ...m, _source: 'MovieMind Database' }))
        
      } else if (currentMode === MODES.ACTOR) {
        const res = await searchPeople(query, 'actor', parsedMinYear, parsedMaxYear, limit)
        data = (res || []).map(m => ({ ...m, _source: 'MovieMind Database' }))
      } else if (currentMode === MODES.DIRECTOR) {
        const res = await searchPeople(query, 'director', parsedMinYear, parsedMaxYear, limit)
        data = (res || []).map(m => ({ ...m, _source: 'MovieMind Database' }))
      }
      
      if (!data || data.length === 0) {
        setError(currentMode === MODES.TITLE ? "Movie not found. Please try another title." : "No matching movies found.")
      } else {
        setResults(data)
      }
    } catch (err) {
      console.error(err)
      setError("An error occurred while searching. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  if (selectedMovie) {
    return (
      <main className="app-container">
        <header className="app-header">
          <h1 className="logo-text"><span>Movie</span>Mind</h1>
          <p className="subtitle">AI-Powered Cinema Discovery</p>
        
          <div className="auth-controls">
              {!isAuthLoading && (
                currentUser ? (
                  <div className="auth-user-section">
                    <div className="welcome-block">
                      <span className="welcome-text">Welcome back,</span>
                      <strong className="username-text">{currentUser.username}</strong>
                    </div>
                    <div className="auth-buttons">
                      <button className="header-btn boxed-btn outline" onClick={() => handleModeChange(MODES.SUGGESTED)}>&#10024; Suggested</button>
                      <button className="header-btn boxed-btn" onClick={() => handleModeChange(MODES.WATCHLIST)}>My Watchlist</button>
                      <button className="header-btn boxed-btn outline" onClick={handleLogout}>Logout</button>
                    </div>
                  </div>
                ) : (
                  <div className="auth-buttons">
                    <button className="header-btn boxed-btn outline" onClick={() => setShowAuthModal('login')}>Login</button>
                    <button className="header-btn boxed-btn" onClick={() => setShowAuthModal('register')}>Register</button>
                  </div>
                )
              )}
            </div>
</header>
        <MovieDetails movie={selectedMovie} onBack={() => setSelectedMovie(null)} />
      
      {showAuthModal && (
        <AuthModal 
          initialMode={showAuthModal === 'login'}
          onClose={() => setShowAuthModal(false)}
          onLoginSuccess={async () => {
            setShowAuthModal(false)
            try {
              const user = await getCurrentUser()
              setCurrentUser(user)
              const savedItems = await getWatchlist()
              setWatchlist(new Set(savedItems.map(item => item.tmdb_id)))
            } catch (err) {
              console.error(err)
            }
          }}
        />
      )}
    </main>
    )
  }

  return (
    <main className="app-container">
      <header className="app-header">
        <h1 className="logo-text"><span>Movie</span>Mind</h1>
        <p className="subtitle">Find a movie from the story you remember.</p>
      
          <div className="auth-controls">
              {!isAuthLoading && (
                currentUser ? (
                  <div className="auth-user-section">
                    <div className="welcome-block">
                      <span className="welcome-text">Welcome back,</span>
                      <strong className="username-text">{currentUser.username}</strong>
                    </div>
                    <div className="auth-buttons">
                      <button className="header-btn boxed-btn outline" onClick={() => handleModeChange(MODES.SUGGESTED)}>&#10024; Suggested</button>
                      <button className="header-btn boxed-btn" onClick={() => handleModeChange(MODES.WATCHLIST)}>My Watchlist</button>
                      <button className="header-btn boxed-btn outline" onClick={handleLogout}>Logout</button>
                    </div>
                  </div>
                ) : (
                  <div className="auth-buttons">
                    <button className="header-btn boxed-btn outline" onClick={() => setShowAuthModal('login')}>Login</button>
                    <button className="header-btn boxed-btn" onClick={() => setShowAuthModal('register')}>Register</button>
                  </div>
                )
              )}
            </div>
</header>

      
        {currentMode === MODES.SUGGESTED && (
          <section className="suggested-section">
            <div className="suggested-header" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', borderBottom: '1px solid var(--border)', paddingBottom: '1.5rem', marginBottom: '1.5rem' }}>
                <div>
                  <h2 style={{ margin: '0 0 0.5rem 0' }}>Suggested Movies For You</h2>
                  <p style={{ color: '#a79cce', margin: 0 }}>Recommendations based on the movies in your watchlist.</p>
                </div>
                <div style={{ display: 'flex' }}>
                  <button className="header-btn boxed-btn outline back-btn" onClick={() => handleModeChange(MODES.STORY)}>&#8592; Back to Discover</button>
                </div>
              </div>
            
            {isLoading && <div className="loading">Loading your personalized suggestions...</div>}
            {!isLoading && error && <div className="error">{error}</div>}
            
            {!isLoading && !error && watchlist.size === 0 && (
              <div className="empty-watchlist">
                <h3>Save a few movies to your watchlist and MovieMind will recommend movies tailored to your taste.</h3>
                <button className="header-btn boxed-btn" style={{ marginTop: '15px' }} onClick={() => handleModeChange(MODES.STORY)}>Discover Movies</button>
              </div>
            )}
            
            {!isLoading && !error && watchlist.size > 0 && suggestedMovies.length === 0 && (
              <div className="empty-watchlist">
                <h3>No recommendations found right now.</h3>
              </div>
            )}
            
            {!isLoading && !error && watchlist.size > 0 && suggestedMovies.length > 0 && (
              <div className="results-grid">
                {suggestedMovies.map(movie => (
                  <MovieCard 
                    key={movie.tmdb_id || movie.tmdbId || movie.id} 
                    movie={movie} 
                    isPlotSearch={false} 
                    onClick={setSelectedMovie}
                    isSaved={watchlist.has(movie.tmdb_id || movie.tmdbId || movie.id)}
                    onToggleWatchlist={handleToggleWatchlist}
                    isWatchlistView={currentMode === MODES.WATCHLIST}
                  />
                ))}
              </div>
            )}
          </section>
        )}

        {currentMode === MODES.WATCHLIST && (
          <section className="watchlist-section">
            <div className="watchlist-header">
              <h2>My Watchlist</h2>
              <button className="header-btn boxed-btn outline back-btn" onClick={() => handleModeChange(MODES.STORY)}>&#8592; Back to Discover</button>
            </div>
            {isLoading && <div className="loading">Loading your watchlist...</div>}
            {currentMode !== MODES.WATCHLIST && error && <div className="error">{error}</div>}
            {!isLoading && !error && watchlistMovies.filter(m => watchlist.has(m.id)).length === 0 && (
              <div className="empty-watchlist">
                <h3>Your watchlist is empty</h3>
                <p>Discover great movies and save them here for later.</p>
                <button className="header-btn boxed-btn" onClick={() => handleModeChange(MODES.STORY)}>Discover Movies</button>
              </div>
            )}
            {!isLoading && watchlistMovies.filter(m => watchlist.has(m.id)).length > 0 && (
              <div className="results-grid">
                {watchlistMovies.filter(m => watchlist.has(m.id)).map(movie => (
                  <MovieCard 
                    key={movie.id} 
                    movie={movie} 
                    isPlotSearch={false} 
                    onClick={setSelectedMovie}
                    isSaved={watchlist.has(movie.tmdb_id || movie.tmdbId || movie.id)}
                    onToggleWatchlist={handleToggleWatchlist}
                    isWatchlistView={currentMode === MODES.WATCHLIST}
                  />
                ))}
              </div>
            )}
          </section>
        )}

        {(currentMode !== MODES.WATCHLIST && currentMode !== MODES.SUGGESTED) && (
          <section className="search-section">

        {/* Modern Tab Selector */}
        <div className="tabs">
          <button className={`tab ${currentMode === MODES.STORY ? 'active' : ''}`} onClick={() => handleModeChange(MODES.STORY)}>Story & Details</button>
          <button className={`tab ${currentMode === MODES.TITLE ? 'active' : ''}`} onClick={() => handleModeChange(MODES.TITLE)}>By Title</button>
          <button className={`tab ${currentMode === MODES.ACTOR ? 'active' : ''}`} onClick={() => handleModeChange(MODES.ACTOR)}>By Actor</button>
          <button className={`tab ${currentMode === MODES.DIRECTOR ? 'active' : ''}`} onClick={() => handleModeChange(MODES.DIRECTOR)}>By Director</button>
        </div>

        <form onSubmit={handleSearch} className="search-form">
          
          <div className="main-input-wrapper">
            {currentMode === MODES.STORY ? (
              <textarea
                className="hero-input"
                rows="3"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Describe the plot, the vibes, or a specific scene you remember..."
              />
            ) : (
              <input
                className="hero-input single-line"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  currentMode === MODES.TITLE ? "e.g. The Dark Knight" :
                  currentMode === MODES.ACTOR ? "e.g. Tom Hanks" :
                  currentMode === MODES.DIRECTOR ? "e.g. Christopher Nolan" : ""
                }
              />
            )}
          </div>

          <div className="advanced-filters-section">
            <button 
              type="button" 
              className="toggle-advanced-btn"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              {showAdvanced ? 'Hide Advanced Filters' : 'Show Advanced Filters'}
            </button>
            
            {showAdvanced && (
              <div className="filters-grid">
                {currentMode === MODES.STORY && (
                  <>
                    <div className="filter-group">
                      <label>Actor</label>
                      <input type="text" value={actor} onChange={(e) => setActor(e.target.value)} placeholder="e.g. Jake Gyllenhaal" />
                    </div>
                    <div className="filter-group">
                      <label>Director</label>
                      <input type="text" value={director} onChange={(e) => setDirector(e.target.value)} placeholder="e.g. Christopher Nolan" />
                    </div>
                    <div className="filter-group">
                      <label>Genre</label>
                      <select value={genre} onChange={(e) => setGenre(e.target.value)}>
                        <option value="">Any genre</option>
                        <option value="Action">Action</option>
                        <option value="Adventure">Adventure</option>
                        <option value="Animation">Animation</option>
                        <option value="Comedy">Comedy</option>
                        <option value="Crime">Crime</option>
                        <option value="Documentary">Documentary</option>
                        <option value="Drama">Drama</option>
                        <option value="Family">Family</option>
                        <option value="Fantasy">Fantasy</option>
                        <option value="History">History</option>
                        <option value="Horror">Horror</option>
                        <option value="Music">Music</option>
                        <option value="Mystery">Mystery</option>
                        <option value="Romance">Romance</option>
                        <option value="Science Fiction">Science Fiction</option>
                        <option value="Thriller">Thriller</option>
                        <option value="War">War</option>
                        <option value="Western">Western</option>
                      </select>
                    </div>
                  </>
                )}
                
                <div className="filter-group" style={{ gridColumn: 'span 2' }}>
                  <label>Release Year Range</label>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <input type="number" min="1900" max="2030" value={minYear} onChange={(e) => setMinYear(e.target.value)} placeholder="From Year" style={{ flex: 1 }} />
                    <span style={{ display: 'flex', alignItems: 'center', color: 'var(--text-secondary)' }}>â€”</span>
                    <input type="number" min="1900" max="2030" value={maxYear} onChange={(e) => setMaxYear(e.target.value)} placeholder="To Year" style={{ flex: 1 }} />
                  </div>
                </div>

                {currentMode === MODES.STORY && (
                  <div className="filter-group">
                    <label>Min Rating</label>
                    <select value={minRating} onChange={(e) => setMinRating(e.target.value)}>
                      <option value="">Any rating</option>
                      <option value="5">5+ / 10</option>
                      <option value="6">6+ / 10</option>
                      <option value="7">7+ / 10</option>
                      <option value="8">8+ / 10</option>
                      <option value="9">9+ / 10</option>
                    </select>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="search-footer">
            <div className="filter-group limit-group">
              <label>Top N</label>
              <input type="number" min="1" max="50" value={limit} onChange={(e) => setLimit(parseInt(e.target.value) || 10)} />
            </div>
            
            <button type="submit" disabled={isLoading} className="btn-search">
              {isLoading ? (
                <span className="spinner-text"><span className="spinner"></span> Searching...</span>
              ) : 'Find Movies'}
            </button>
          </div>
        </form>
      </section>
      )}

      {currentMode !== MODES.WATCHLIST && currentMode !== MODES.SUGGESTED && error && (
        <div className="state-message error">
          <div className="icon">âš ï¸</div>
          <p>{error}</p>
        </div>
      )}
      
      {currentMode !== MODES.WATCHLIST && currentMode !== MODES.SUGGESTED && isLoading && (
        <div className="state-message loading">
          <div className="spinner-large"></div>
          <p>Analyzing cinematic vectors...</p>
        </div>
      )}

      {currentMode !== MODES.WATCHLIST && currentMode !== MODES.SUGGESTED && !isLoading && results.length > 0 && (
        <section className="results-section">
          <h2>
            {requestedQuery 
              ? `Top Matches for "${requestedQuery}"` 
              : `Top ${results.length} Matches Found`}
          </h2>
          <div className="movie-list">
            {results.map((movie) => (
              <MovieCard 
                key={movie.tmdb_id || movie.tmdbId || movie.id} 
                movie={movie} 
                isPlotSearch={currentMode === MODES.STORY} 
                onClick={setSelectedMovie}
                isSaved={watchlist.has(movie.tmdb_id || movie.tmdbId || movie.id)}
                onToggleWatchlist={handleToggleWatchlist}
                    isWatchlistView={currentMode === MODES.WATCHLIST}
              />
            ))}
          </div>
        </section>
      )}
    
      {showAuthModal && (
        <AuthModal 
          initialMode={showAuthModal === 'login'}
          onClose={() => setShowAuthModal(false)}
          onLoginSuccess={async () => {
            setShowAuthModal(false)
            try {
              const user = await getCurrentUser()
              setCurrentUser(user)
              const savedItems = await getWatchlist()
              setWatchlist(new Set(savedItems.map(item => item.tmdb_id)))
            } catch (err) {
              console.error(err)
            }
          }}
        />
      )}
    </main>
  )
}

export default App



