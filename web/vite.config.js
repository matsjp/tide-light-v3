import { defineConfig } from 'vite'

export default defineConfig({
  base: './',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'leaflet': ['leaflet']
        }
      }
    }
  },
  server: {
    port: 5173,
    open: true
  }
})
