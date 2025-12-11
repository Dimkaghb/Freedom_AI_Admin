import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    }
  },
server: {
    host: true, // allows Vite to be accessed via network IP/domain
    port: 3000,
    hmr: {
      host: 'freedom-analysis-admin.chocodev.kz',
      protocol: 'ws',
      port: 3000
    }
  }
})
