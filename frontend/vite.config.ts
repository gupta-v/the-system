import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: true, // listen on the LAN too, so a phone on the same network/hotspot can open it
    strictPort: true, // fail loudly instead of drifting to 5174+ (the run script checks this port)
    // Same origin as the app, so the httpOnly session cookie just works (no CORS).
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
        // Log each API call in this terminal: time, method, path, status, duration.
        configure: (proxy) => {
          const started = new WeakMap<object, number>()
          proxy.on('proxyReq', (_proxyReq, req) => started.set(req, Date.now()))
          proxy.on('proxyRes', (res, req) => {
            const ms = Date.now() - (started.get(req) ?? Date.now())
            const time = new Date().toLocaleTimeString()
            console.log(`${time} [api] ${req.method} ${req.url} -> ${res.statusCode} (${ms} ms)`)
          })
        },
      },
    },
  },
})
