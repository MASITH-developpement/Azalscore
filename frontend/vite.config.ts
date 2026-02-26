import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import path from 'path';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.png', 'apple-touch-icon.png'],
      manifest: {
        name: 'AZALSCORE',
        short_name: 'AZALSCORE',
        description: 'ERP SaaS Multi-tenant - Gestion d\'entreprise',
        lang: 'fr',
        theme_color: '#1E6EFF',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'any',
        start_url: '/',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        skipWaiting: true,
        clientsClaim: true,
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\./i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 // 1 hour
              }
            }
          }
        ]
      }
    })
  ],
  resolve: {
    alias: {
      '@core': path.resolve(__dirname, './src/core'),
      '@ui': path.resolve(__dirname, './src/ui-engine'),
      '@modules': path.resolve(__dirname, './src/modules'),
      '@routing': path.resolve(__dirname, './src/routing'),
      '@security': path.resolve(__dirname, './src/security'),
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      // Routes API versionnées
      '/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/v2': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/v3': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // Routes API legacy (sans préfixe de version)
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      // Routes métier (v3 CRUDRouter)
      '/interventions': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/commercial': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/hr': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/inventory': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/projects': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/accounting': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/treasury': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/purchases': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          query: ['@tanstack/react-query', 'axios'],
          ui: ['zustand', 'react-hook-form', 'zod']
        }
      }
    }
  }
});
