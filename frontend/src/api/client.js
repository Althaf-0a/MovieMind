import axios from 'axios'

// Shared Axios client for all MovieMind backend requests.
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 5000,
})

export default apiClient
