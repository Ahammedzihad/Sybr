import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/auth': 'http://localhost:8001',
      '/admin': 'http://localhost:8001',
      '/conversations': 'http://localhost:8001',
      '/customer': 'http://localhost:8001',
      '/health': 'http://localhost:8001',
      '/analyze': 'http://localhost:8001',
      '/copilot': 'http://localhost:8001',
      '/upload': 'http://localhost:8001',
      '/trends': 'http://localhost:8001',
      '/dashboard': 'http://localhost:8001',
      '/issues': 'http://localhost:8001',
      '/eval': 'http://localhost:8001',
      '/gmail': 'http://localhost:8001',
    },
  },
})
