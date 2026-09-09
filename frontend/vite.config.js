import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// Im Container liefert FastAPI die gebauten Dateien aus, deshalb wird der
// Proxy nur fuer die lokale Entwicklung (npm run dev) benoetigt.
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  build: { outDir: 'dist', emptyOutDir: true },
  server: {
    host: true,
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8000' }
  }
})
