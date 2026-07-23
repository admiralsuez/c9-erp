import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Dev server: forward /api/* to the local backend, stripping the /api prefix
      // (backend routes are unprefixed: /auth, /settings, /users, ...)
      '/api': {
        target: process.env.VITE_API_PROXY_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
