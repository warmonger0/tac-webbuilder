import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import dotenv from 'dotenv'
import path from 'path'

// Load environment variables from .ports.env
dotenv.config({ path: path.resolve(__dirname, '../../.ports.env') })

const frontendPort = parseInt(process.env.FRONTEND_PORT || '9213')
const backendUrl = process.env.VITE_BACKEND_URL || 'http://localhost:9113'
const backendWsUrl = backendUrl.replace(/^http/, 'ws')

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: frontendPort,
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
      },
      '/ws': {
        target: backendWsUrl,
        ws: true,
      },
    },
  },
})
