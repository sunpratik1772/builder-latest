import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

// Keep aliases here in sync with compilerOptions.paths in tsconfig.json.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@nodes': path.resolve(__dirname, 'src/nodes'),
      '@store': path.resolve(__dirname, 'src/store'),
      '@services': path.resolve(__dirname, 'src/services'),
      '@components': path.resolve(__dirname, 'src/components'),
      '@styles': path.resolve(__dirname, 'src/styles'),
      '@types': path.resolve(__dirname, 'src/types'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    allowedHosts: true,
    hmr: {
      clientPort: 443,
      protocol: 'wss',
    },
    proxy: {
      // In dev: requests to /api/* hit local FastAPI on 8001.
      // In Kubernetes preview: ingress already routes /api/* → backend:8001
      // so this proxy block is a no-op for the deployed preview URL.
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
