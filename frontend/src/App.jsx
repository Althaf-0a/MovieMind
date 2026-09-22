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

const MODES = {
  STORY: 'STORY',
  TITLE: 'TITLE',
  ACTOR: 'ACTOR',
  DIRECTOR: 'DIRECTOR',
}

function App() {
  const [currentMode, setCurrentMode] = useState(MODES.STORY)
  const [query, setQuery] = useState('')
  const [actor, setActor] = useState('')
  const [director, setDirector] = useState('')
  const [genre, setGenre] = useState('')
  const [year, setYear] = useState('')
  const [minRating, setMinRating] = useState('')
  const [limit, setLimit] = useState(10)
  
  const [showAdvanced, setShowAdvanced] = useState(false)
  
  const [results, setResults] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const [requestedQuery, setRequestedQuery] = useState('')
  const [selectedMovie, setSelectedMovie] = useState(null)

  const handleModeChange = (mode) => {
    setCurrentMode(mode)
    setQuery('')
    setResults([])
    setError(null)
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim() && currentMode !== MODES.STORY && !actor.trim() && !director.trim()) return

    setIsLoading(true)
    setError(null)
    setResults([])
    setRequestedQuery(query)
    setSelectedMovie(null)

    try {
      let data = []
      if (currentMode === MODES.STORY) {
        const response = await searchHybridDiscovery({
          plot: query,
          actor: actor,
          director: director,
          genre: genre,
          year: year ? parseInt(year) : null,
          min_rating: minRating ? parseFloat(minRating) : null,
          top_n: limit
        })
        data = (response.results || []).map(m => ({ ...m, _source: 'MovieMind Database' }))
      } else if (currentMode === MODES.TITLE) {
        // Fallback logic
        const localSearch = await searchMovies(query, 1)
        if (localSearch && localSearch.length > 0) {
          const relatedData = await getRelatedMovies(localSearch[0].tmdbId)
          if (relatedData && relatedData.source_movie) {
            data = [{ ...relatedData.source_movie, _source: 'MovieMind Database', _is_main: true }]
          }
        } else {
          const tmdbSearch = await searchTMDBMovies(query, 1)
          if (tmdbSearch && tmdbSearch.results && tmdbSearch.results.length > 0) {
            const relatedData = await getRelatedMovies(tmdbSearch.results[0].id)
            if (relatedData && relatedData.source_movie) {
              data = [{ ...relatedData.source_movie, _source: 'TMDB', _is_main: true }]
            }
          }
        }
      } else if (currentMode === MODES.ACTOR) {
        const res = await searchPeople(query, 'actor', limit)
        data = (res || []).map(m => ({ ...m, _source: 'MovieMind Database' }))
      } else if (currentMode === MODES.DIRECTOR) {
        const res = await searchPeople(query, 'director', limit)
        data = (res || []).map(m => ({ ...m, _source: 'MovieMind Database' }))
      }
      
      if (!data || data.length === 0) {
        setError(currentMode === MODES.TITLE ? "No movies found on TMDB for that query." : "No matching movies found.")
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
        </header>
        <MovieDetails movie={selectedMovie} onBack={() => setSelectedMovie(null)} />
      </main>
    )
  }

  return (
    <main className="app-container">
      <header className="app-header">
        <h1 className="logo-text"><span>Movie</span>Mind</h1>
        <p className="subtitle">Find a movie from the story you remember.</p>
      </header>

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

          {currentMode === MODES.STORY && (
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
                  <div className="filter-group">
                    <label>Release Year</label>
                    <input type="number" min="1900" max="2030" value={year} onChange={(e) => setYear(e.target.value)} placeholder="Any year" />
                  </div>
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
                </div>
              )}
            </div>
          )}

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

      {error && (
        <div className="state-message error">
          <div className="icon">⚠️</div>
          <p>{error}</p>
        </div>
      )}
      
      {isLoading && (
        <div className="state-message loading">
          <div className="spinner-large"></div>
          <p>Analyzing cinematic vectors...</p>
        </div>
      )}

      {!isLoading && results.length > 0 && (
        <section className="results-section">
          <h2>
            {requestedQuery 
              ? `Top Matches for "${requestedQuery}"` 
              : `Top ${results.length} Matches Found`}
          </h2>
          <div className="movie-list">
            {results.map((movie) => (
              <MovieCard 
                key={movie.id || movie.tmdbId} 
                movie={movie} 
                isPlotSearch={currentMode === MODES.STORY} 
                onClick={setSelectedMovie}
              />
            ))}
          </div>
        </section>
      )}
    </main>
  )
}

export default App
