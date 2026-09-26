import axios from 'axios'

/** Dev backend runs on the same machine as Vite, so follow the host in the URL bar
 *  (localhost on this Mac, LAN IP when testing from a phone).
 *  Production is pinned by VITE_API_BASE_URL in the Dockerfile / cloudbuild. */
export function getApiBaseURL() {
  if (import.meta.env.VITE_API_BASE_URL) return import.meta.env.VITE_API_BASE_URL
  if (import.meta.env.DEV) return `http://${window.location.hostname}:5015/api`
  return 'https://backend.grainstoryfarm.ca/api'
}

const apiClient = axios.create({
  baseURL: getApiBaseURL(),
  timeout: 30000, // Increased to 30 seconds
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('admin_auth_token')
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
      localStorage.removeItem('admin_auth_token')
      localStorage.removeItem('admin_user')
      localStorage.removeItem('admin_auth_token_expires_at')

      // Only redirect if not already on login page and not in router guard
      if (window.location.pathname !== '/login' && !error.config?.skipRedirect) {
        import('../router').then(({ default: router }) => {
          router.replace('/login')
        })
      }
    }

    // Handle errors globally
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default apiClient

