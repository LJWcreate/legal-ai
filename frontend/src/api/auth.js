import api from '../api/client'

export async function register(payload) {
  return api.post('/auth/register', payload)
}

export async function login(payload) {
  const data = await api.post('/auth/login', payload)
  localStorage.setItem('access_token', data.access_token)
  localStorage.setItem('refresh_token', data.refresh_token)
  return data
}

export function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export async function me() {
  return api.get('/auth/me')
}
