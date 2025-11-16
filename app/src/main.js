import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { checkAuth } from './utils/auth'

// Initialize app
const app = createApp(App)

// Check authentication on app start
checkAuth().then((isAuthenticated) => {
  if (isAuthenticated) {
    console.log('✅ User authenticated from cached token')
  } else {
    console.log('ℹ️  No valid cached token, user needs to login')
  }
})

app.use(router)
app.mount('#app')

