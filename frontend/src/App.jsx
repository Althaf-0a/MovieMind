import { useState } from 'react'
import { 
  getRecommendations, 
  searchMovies, 
  searchPeople,
  searchTMDBMovies,
  getRelatedMovies,
  searchHybridDiscovery
} from './services/api'
import MovieCard from './components/MovieCard'
import MovieDetails from './components/MovieDetails'
import './App.css'

function App() {
  // Define search modes
  const MODES = {
    STORY: 'STORY',
    SIMILAR: 'SIMILAR',
    TITLE: 'TITLE',
    ACTOR: 'ACTOR',
    DIRECTOR: 'DIRECTOR'
  };

  const [currentMode, setCurrentMode] = useState(MODES.STORY)
  const [query, setQuery] = useState('')
  const [limit, setLimit] = useState(10)

  // Hybrid Discovery Optional Fields
  const [actor, setActor] = useState('')
  const [director, setDirector] = useState('')
  const [genre, setGenre] = useState('')
  const [year, setYear] = useState('')
  const [minRating, setMinRating] = useState('')

  // UI state
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  // Results
  const [results, setResults] = useState([])
  const [requestedQuery, setRequestedQuery] = useState('')
  const [selectedMovie, setSelectedMovie] = useState(null)

  // Handle mode changes cleanly
  const handleModeChange = (e) => {
    setCurrentMode(e.target.value)
    setQuery('')
    setActor('')
    setDirector('')
    setGenre('')
    setYear('')
    setMinRating('')
    setResults([])
    setError(null)
    setRequestedQuery('')
  }

  // Unified form submission
  const handleSearch = async (e) => {
    e.preventDefault()
    
    setError(null)
    setResults([])
    setRequestedQuery('')

    if (!query.trim() && currentMode !== MODES.STORY) {
      setError("Please describe the type of movie you're looking for or enter a valid search.")
      return
    }

    if (currentMode === MODES.STORY && !query.trim() && !actor.trim() && !director.trim() && !genre && !year && !minRating) {
      setError("Please provide at least one search criterion.")
      return
    }

    setIsLoading(true)

    try {
      let data = [];
      
      // Determine which API to call based on the selected mode
      switch(currentMode) {
        case MODES.STORY:
          const response = await searchHybridDiscovery({
            plot: query.trim() || null,
            actor: actor.trim() || null,
            director: director.trim() || null,
            genre: genre || null,
            year: year ? parseInt(year) : null,
            min_rating: minRating ? parseFloat(minRating) : null,
            top_n: limit
          });
          data = (response.results || []).map(m => ({ ...m, _source: 'MovieMind Database' }));
          setResults(data);
          break;
        case MODES.SIMILAR:
          data = await getRecommendations(query, limit);
          data = (data.recommendations || []).map(m => ({ ...m, _source: 'MovieMind Database' }));
          setResults(data);
          break;
        case MODES.TITLE:
          // 1. Check local catalog first
          const localSearch = await searchMovies(query, 1);
          if (localSearch && localSearch.length > 0) {
            const bestLocal = localSearch[0];
            // Get related movies using its TMDB ID
            const relatedData = await getRelatedMovies(bestLocal.tmdbId);
            if (relatedData && relatedData.source_movie) {
              const mainMovie = { ...relatedData.source_movie, _source: 'MovieMind Database', _is_main: true };
              const related = (relatedData.related_movies || []).map(m => ({
                ...m,
                _source: 'TMDB'
              }));
              setResults([mainMovie, ...related]);
              break;
            }
          }
          
          // 2. If no local match, search TMDB directly
          const tmdbSearch = await searchTMDBMovies(query, 1);
          if (!tmdbSearch || !tmdbSearch.results || tmdbSearch.results.length === 0) {
            setError("No movies found on TMDB for that query.");
            setResults([]);
            break;
          }
          const bestMovie = tmdbSearch.results[0];
          const relatedData = await getRelatedMovies(bestMovie.id);
          if (relatedData && relatedData.source_movie) {
            const mainMovie = { ...relatedData.source_movie, _source: 'TMDB', _is_main: true };
            const related = (relatedData.related_movies || []).map(m => ({
              ...m,
              _source: 'TMDB'
            }));
            setResults([mainMovie, ...related]);
          } else {
            setResults([{ ...bestMovie, _source: 'TMDB', _is_main: true }]);
          }
          break;
        case MODES.ACTOR:
          data = await searchPeople(query, 'actor', limit);
          data = (data || []).map(m => ({ ...m, _source: 'MovieMind Database' }));
          setResults(data);
          break;
        case MODES.DIRECTOR:
          data = await searchPeople(query, 'director', limit);
          data = (data || []).map(m => ({ ...m, _source: 'MovieMind Database' }));
          setResults(data);
          break;
        default:
          break;
      }
      
      setRequestedQuery(currentMode === MODES.STORY ? (query || actor || director || "Filtered Search") : query)
      
      // We check if data array is empty directly if not title search
      if (currentMode !== MODES.TITLE && (!data || data.length === 0)) {
        setError("No movies found. Please try a different search.")
      }

    } catch (err) {
      if (err.response && err.response.status === 404) {
        setError("No movies found for this query.")
      } else if (err.response && err.response.status === 400) {
        setError(err.response.data.detail || "Invalid input parameters provided.")
      } else if (err.response && err.response.status === 422) {
        setError("Invalid input parameters provided.")
      } else {
        setError("Unable to connect to the MovieMind backend.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  if (selectedMovie) {
    return (
      <main className="container">
        <header className="header">
          <h1>MovieMind</h1>
          <p>AI Movie Recommendation System</p>
        </header>
        <MovieDetails movie={selectedMovie} onBack={() => setSelectedMovie(null)} />
      </main>
    )
  }

  return (
    <main className="container">
      <header className="header">
        <h1>MovieMind</h1>
        <p>AI Movie Recommendation System</p>
      </header>

      <section className="search-section">
        {/* Mode Selector */}
        <div className="mode-selector">
          <label htmlFor="mode">Search Mode: </label>
          <select id="mode" value={currentMode} onChange={handleModeChange}>
            <option value={MODES.STORY}>Find a Movie by Story</option>
            <option value={MODES.TITLE}>Movie Title</option>
            <option value={MODES.SIMILAR}>Similar Movies (AI)</option>
            <option value={MODES.ACTOR}>Actor Name</option>
            <option value={MODES.DIRECTOR}>Director Name</option>
          </select>
        </div>

        <form onSubmit={handleSearch} className="search-form">
          {currentMode === MODES.STORY ? (
            <div className="hybrid-search-form">
              <div className="input-group">
                <label htmlFor="searchQuery" style={{fontSize: '1.1rem', fontWeight: 'bold'}}>Describe the movie plot</label>
                <textarea
                  id="searchQuery"
                  rows="4"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g. A detective investigates a mysterious murder in a small town and discovers a connection to an old case."
                  style={{width: '100%', marginBottom: '15px'}}
                />
              </div>

              <div style={{marginBottom: '10px'}}><strong>Optional clues:</strong></div>
              
              <div style={{display: 'flex', flexWrap: 'wrap', gap: '15px'}}>
                <div className="input-group" style={{flex: '1 1 45%'}}>
                  <label htmlFor="actorInput">Actor / Actress</label>
                  <input
                    id="actorInput"
                    type="text"
                    value={actor}
                    onChange={(e) => setActor(e.target.value)}
                    placeholder="e.g. Jake Gyllenhaal"
                  />
                </div>
                
                <div className="input-group" style={{flex: '1 1 45%'}}>
                  <label htmlFor="directorInput">Director</label>
                  <input
                    id="directorInput"
                    type="text"
                    value={director}
                    onChange={(e) => setDirector(e.target.value)}
                    placeholder="e.g. Christopher Nolan"
                  />
                </div>
                
                <div className="input-group" style={{flex: '1 1 30%'}}>
                  <label htmlFor="genreInput">Genre</label>
                  <select id="genreInput" value={genre} onChange={(e) => setGenre(e.target.value)}>
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
                
                <div className="input-group" style={{flex: '1 1 30%'}}>
                  <label htmlFor="yearInput">Release Year</label>
                  <input
                    id="yearInput"
                    type="number"
                    min="1900"
                    max="2030"
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                    placeholder="Any year"
                  />
                </div>
                
                <div className="input-group" style={{flex: '1 1 30%'}}>
                  <label htmlFor="ratingInput">Minimum Rating</label>
                  <select id="ratingInput" value={minRating} onChange={(e) => setMinRating(e.target.value)}>
                    <option value="">Any rating</option>
                    <option value="5">5+ / 10</option>
                    <option value="6">6+ / 10</option>
                    <option value="7">7+ / 10</option>
                    <option value="8">8+ / 10</option>
                    <option value="9">9+ / 10</option>
                  </select>
                </div>
              </div>
            </div>
          ) : (
            <div className="input-group">
              <label htmlFor="searchQuery">
                {currentMode === MODES.SIMILAR && 'Enter a movie title to find similar films'}
                {currentMode === MODES.TITLE && 'Enter a movie title to search'}
                {currentMode === MODES.ACTOR && 'Enter an actor or actress name'}
                {currentMode === MODES.DIRECTOR && 'Enter a director name'}
              </label>
              
              <input
                id="searchQuery"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={
                  currentMode === MODES.SIMILAR ? "e.g. The Dark Knight" :
                  currentMode === MODES.TITLE ? "e.g. Avengers" :
                  currentMode === MODES.ACTOR ? "e.g. Tom Hanks" :
                  currentMode === MODES.DIRECTOR ? "e.g. Christopher Nolan" : ""
                }
              />
            </div>
          )}
          
          <div className="input-group limit-group" style={{marginTop: '15px'}}>
            <label htmlFor="limit">Top N Results</label>
            <input
              id="limit"
              type="number"
              min="1"
              max={currentMode === MODES.STORY ? 50 : 50}
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value) || 10)}
            />
          </div>

          <button type="submit" disabled={isLoading} className="btn-recommend" style={{marginTop: '10px'}}>
            {isLoading ? 'Searching...' : (currentMode === MODES.STORY ? 'Find Movies' : 'Search')}
          </button>
        </form>
      </section>

      {/* State Messages */}
      {error && <div className="error-message">{error}</div>}
      {isLoading && <div className="loading-message">Fetching results from the backend...</div>}

      {/* Results Display */}
      {!isLoading && results.length > 0 && (
        <section className="results-section">
          <h2>Results for "{requestedQuery}"</h2>
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
