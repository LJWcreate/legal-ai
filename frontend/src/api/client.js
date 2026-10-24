import axios from 'axios'
import router from '../router'

const api = axios.create({ baseURL: '/api/v1' })

// 请求拦截：附 JWT
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截：401 统一跳登录
api.interceptors.response.use(
  (resp) => resp.data,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      router.push('/login')
    }
    return Promise.reject(error)
  },
)

export default api
