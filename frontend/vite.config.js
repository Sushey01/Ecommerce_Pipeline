import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),
    react(),
  ],
  server: {
    port: 5173,
    proxy: {
      '/health':     { target: 'http://localhost:8005', changeOrigin: true },
      '/predict':    { target: 'http://localhost:8005', changeOrigin: true },
      '/monitoring': { target: 'http://localhost:8005', changeOrigin: true },
      '/drift':      { target: 'http://localhost:8005', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
