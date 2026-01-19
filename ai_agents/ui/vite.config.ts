import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 80,
    // Configure HMR WebSocket explicitly for port 80
    hmr: {
      host: 'localhost',
      port: 80,
      protocol: 'ws',
    },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:81',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'http://127.0.0.1:81',
        changeOrigin: true,
        secure: false,
        ws: true, // Enable WebSocket proxying
      },
    },
  },
})
