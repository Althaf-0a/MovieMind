import axios from 'axios';

// Keep the backend base URL centralized.
const API_BASE_URL = 'http://127.0.0.1:8000/api';

/**
 * Fetches movie recommendations (Similar Movies mode).
 */
export const getRecommendations = async (movieTitle, topN = 10) => {
  const response = await axios.get(`${API_BASE_URL}/recommendations`, {
    params: {
      movie_title: movieTitle,
      top_n: topN
    }
  });
  return response.data;
};

/**
 * Searches for a movie by its title.
 */
export const searchMovies = async (query, limit = 50) => {
  const response = await axios.get(`${API_BASE_URL}/search/movies`, {
    params: {
      query: query,
      limit: limit
    }
  });
  return response.data;
};

/**
 * Searches for a movie by its title on TMDB.
 */
export const searchTMDBMovies = async (query, page = 1) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tmdb/movies/search`, {
      params: { query, page }
    });
    return response.data;
  } catch (error) {
    console.error("Error searching TMDB movies:", error);
    return { results: [] };
  }
};

export const getRelatedMovies = async (tmdbId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tmdb/movies/${tmdbId}/related`);
    return response.data;
  } catch (error) {
    console.error("Error fetching related movies:", error);
    return null;
  }
};

export const getTmdbMovieDetails = async (tmdbId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/tmdb/movies/${tmdbId}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching TMDB movie details:", error);
    return null;
  }
};

export const getLocalMovieDetails = async (tmdbId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/movies/${tmdbId}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching local movie details:", error);
    return null;
  }
};

/**
 * Hybrid Movie Discovery
 */
export const searchHybridDiscovery = async (params) => {
  const response = await axios.post(`${API_BASE_URL}/discovery/search`, params);
  return response.data;
};

/**
 * Searches for movies by actor or director name.
 */
export const searchPeople = async (query, role = 'all', limit = 50) => {
  const response = await axios.get(`${API_BASE_URL}/search/people`, {
    params: {
      query: query,
      role: role,
      limit: limit
    }
  });
  return response.data;
};

/**
 * Searches for movies using a natural language plot description.
 */
export const searchPlot = async (query, limit = 10) => {
  const response = await axios.get(`${API_BASE_URL}/search/plot`, {
    params: {
      query: query,
      limit: limit
    }
  });
  return response.data;
};

/**
 * Browses the movie catalog with filters.
 */
export const getMovies = async (page = 1, limit = 20, genre, year, minRating, minVotes, sortBy) => {
  const response = await axios.get(`${API_BASE_URL}/movies`, {
    params: {
      page,
      limit,
      genre,
      year,
      min_rating: minRating,
      min_votes: minVotes,
      sort_by: sortBy
    }
  });
  return response.data;
};
