import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/auth': 'http://localhost:8000',
      '/admin': 'http://localhost:8000',
      '/conversations': 'http://localhost:8000',
      '/customer': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
      '/analyze': 'http://localhost:8000',
      '/copilot': 'http://localhost:8000',
      '/upload': 'http://localhost:8000',
      '/trends': 'http://localhost:8000',
      '/dashboard': 'http://localhost:8000',
      '/issues': 'http://localhost:8000',
      '/eval': 'http://localhost:8000',
      '/gmail': 'http://localhost:8000',
    },
  },
})
