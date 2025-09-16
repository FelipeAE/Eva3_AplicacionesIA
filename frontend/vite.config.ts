import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/accounts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/admin-panel': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/contextos': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  },
  build: {
    outDir: 'build',
    assetsDir: 'static',
  },
  define: {
    global: 'globalThis',
  }
})