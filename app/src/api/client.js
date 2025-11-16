import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized - token expired or invalid
    if (error.response && error.response.status === 401) {
      // Clear invalid token
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
      localStorage.removeItem('auth_token_expires_at')
      
      // Only redirect if not already on login page and not in router guard
      // (router guard will handle the redirect)
      if (window.location.pathname !== '/login' && !error.config?.skipRedirect) {
        window.location.href = '/login'
      }
    }
    
    // Handle errors globally
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default apiClient

