import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://64.227.191.1:5173',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path,
      },
    },
  },
})
