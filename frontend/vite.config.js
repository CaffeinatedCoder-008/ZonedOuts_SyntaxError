import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// The production build is plain static files. They are written straight into the
// Flask folder (backend/static), which Flask serves, so Gasper never needs Node.
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
  },
  // `npm run dev`: run Flask on 127.0.0.1:5000 as well. These proxies keep the
  // login cookie on one origin, so sign-in works while you edit the UI.
  server: {
    proxy: {
      '/gmail': 'http://127.0.0.1:5000',
      '/auth': 'http://127.0.0.1:5000',
    },
  },
})
