import apiClient from './client'

export async function getHealth() {
  const response = await apiClient.get('/api/health')
  return response.data
}
