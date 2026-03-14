import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        configure: (proxy) => {
          proxy.on('error', (err) => {
            if (!['ECONNRESET', 'ECONNREFUSED'].includes(err.code)) console.warn('[api proxy]', err.message)
          })
        },
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        configure: (proxy) => {
          proxy.on('error', (err) => {
            if (!['ECONNRESET', 'ECONNREFUSED'].includes(err.code)) console.warn('[ws proxy]', err.message)
          })
        },
      },
    },
  },
})
