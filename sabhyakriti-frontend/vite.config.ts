import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 5173,
      proxy: {
        // Auth + JWKS
        '/api/v1/auth': { target: 'http://localhost:8001', changeOrigin: true },
        '/auth/.well-known': { target: 'http://localhost:8001', changeOrigin: true },
        // Product, Categories, Reviews, Media
        '/api/v1/products': { target: 'http://localhost:8002', changeOrigin: true },
        '/api/v1/categories': { target: 'http://localhost:8002', changeOrigin: true },
        '/api/v1/reviews': { target: 'http://localhost:8002', changeOrigin: true },
        '/api/v1/media': { target: 'http://localhost:8002', changeOrigin: true },
        // Cart, Wishlist
        '/api/v1/cart': { target: 'http://localhost:8003', changeOrigin: true },
        '/api/v1/wishlist': { target: 'http://localhost:8003', changeOrigin: true },
        // Orders, Addresses
        '/api/v1/orders': { target: 'http://localhost:8004', changeOrigin: true },
        '/api/v1/addresses': { target: 'http://localhost:8004', changeOrigin: true },
        // Payments
        '/api/v1/payments': { target: 'http://localhost:8005', changeOrigin: true },
        // Admin BFF (dashboard, reports, customers + all proxied admin routes)
        '/api/v1/admin': { target: 'http://localhost:8007', changeOrigin: true },
        // User profile
        '/api/v1/users': { target: 'http://localhost:8001', changeOrigin: true },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom', 'react-router-dom'],
            redux: ['@reduxjs/toolkit', 'react-redux'],
            ui: ['lucide-react', 'react-hot-toast'],
          },
        },
      },
    },
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: './src/tests/setup.ts',
    },
  };
});
