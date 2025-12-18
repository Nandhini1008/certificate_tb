import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(() => {
  // Get port from environment variable (for Vercel/build time) or use default
  const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 5173
  
  return {
    plugins: [react()],
    server: {
      host: true,
      port: port,
    },
  }
})
