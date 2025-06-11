// frontend/performance_optimizations/optimized_vite.config.ts
/**
 * Optimized Vite configuration for maximum performance.
 * Includes bundle splitting, compression, and advanced optimizations.
 */

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { TanStackRouterVite } from '@tanstack/router-vite-plugin'
import { resolve } from 'path'
import { visualizer } from 'rollup-plugin-visualizer'
import { compression } from 'vite-plugin-compression2'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const isProduction = mode === 'production'
  
  return {
    plugins: [
      react({
        // Enable React Refresh and optimize JSX
        fastRefresh: true,
        jsxImportSource: '@emotion/react',
      }),
      
      TanStackRouterVite(),
      
      // PWA for caching and offline support
      VitePWA({
        registerType: 'autoUpdate',
        workbox: {
          globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
          runtimeCaching: [
            {
              urlPattern: /^https:\/\/api\./,
              handler: 'NetworkFirst',
              options: {
                cacheName: 'api-cache',
                cacheableResponse: {
                  statuses: [0, 200],
                },
                networkTimeoutSeconds: 10,
              },
            },
            {
              urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
              handler: 'CacheFirst',
              options: {
                cacheName: 'images-cache',
                expiration: {
                  maxEntries: 100,
                  maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
                },
              },
            },
          ],
        },
      }),
      
      // Compression for production
      isProduction && compression({
        algorithm: 'gzip',
        exclude: [/\.(br)$/, /\.(gz)$/],
        threshold: 1024,
        compressionOptions: { level: 9 },
      }),
      
      isProduction && compression({
        algorithm: 'brotliCompress',
        exclude: [/\.(br)$/, /\.(gz)$/],
        threshold: 1024,
      }),
      
      // Bundle analyzer
      isProduction && visualizer({
        filename: 'dist/bundle-analysis.html',
        open: false,
        gzipSize: true,
        brotliSize: true,
      }),
    ].filter(Boolean),

    // Optimized build configuration
    build: {
      target: 'es2020',
      outDir: 'dist',
      assetsDir: 'assets',
      sourcemap: !isProduction,
      minify: isProduction ? 'esbuild' : false,
      
      // Advanced chunk splitting strategy
      rollupOptions: {
        output: {
          // Manual chunk splitting for optimal caching
          manualChunks: {
            // React ecosystem
            'react-vendor': [
              'react',
              'react-dom',
              'react-router-dom',
              '@tanstack/react-router',
            ],
            
            // UI libraries
            'ui-vendor': [
              '@chakra-ui/react',
              '@chakra-ui/icons',
              '@emotion/react',
              '@emotion/styled',
              'framer-motion',
            ],
            
            // Data fetching and state management
            'data-vendor': [
              '@tanstack/react-query',
              'axios',
              'zustand',
            ],
            
            // Utilities
            'utils-vendor': [
              'jwt-decode',
              'react-hook-form',
              'react-icons',
              'clsx',
              'class-variance-authority',
            ],
            
            // Forms and validation
            'forms-vendor': [
              'react-hook-form',
              'form-data',
            ],
          },
          
          // Optimize chunk naming for caching
          chunkFileNames: (chunkInfo) => {
            if (chunkInfo.name && chunkInfo.name.includes('vendor')) {
              return 'js/vendor/[name].[hash].js'
            }
            return 'js/[name].[hash].js'
          },
          
          assetFileNames: (assetInfo) => {
            const info = assetInfo.name?.split('.') || []
            const ext = info[info.length - 1]
            
            if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(assetInfo.name || '')) {
              return 'images/[name].[hash][extname]'
            }
            if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name || '')) {
              return 'fonts/[name].[hash][extname]'
            }
            if (ext === 'css') {
              return 'css/[name].[hash].css'
            }
            return 'assets/[name].[hash][extname]'
          },
        },
        
        // External dependencies (for CDN loading if needed)
        external: isProduction ? [] : undefined,
      },
      
      // Chunk size warning threshold
      chunkSizeWarningLimit: 1000,
      
      // CSS code splitting
      cssCodeSplit: true,
      
      // CSS minification
      cssMinify: isProduction,
      
      // Report compressed size
      reportCompressedSize: isProduction,
    },

    // Development server optimization
    server: {
      port: 5173,
      host: true,
      strictPort: true,
      
      // Enable HMR optimizations
      hmr: {
        overlay: true,
      },
      
      // Proxy API calls in development
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false,
        },
      },
    },

    // Preview server (for testing production builds)
    preview: {
      port: 4173,
      host: true,
    },

    // Dependency optimization
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        '@chakra-ui/react',
        '@emotion/react',
        '@emotion/styled',
        'framer-motion',
        '@tanstack/react-query',
        '@tanstack/react-router',
        'axios',
        'zustand',
      ],
      exclude: [
        // Exclude large dependencies that should be loaded separately
        '@tanstack/react-query-devtools',
        '@tanstack/router-devtools',
      ],
    },

    // Resolve configuration
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        '@components': resolve(__dirname, 'src/components'),
        '@hooks': resolve(__dirname, 'src/hooks'),
        '@stores': resolve(__dirname, 'src/stores'),
        '@utils': resolve(__dirname, 'src/utils'),
        '@styles': resolve(__dirname, 'src/styles'),
        '@types': resolve(__dirname, 'src/types'),
      },
    },

    // Environment variables
    define: {
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
    },

    // CSS processing
    css: {
      modules: {
        localsConvention: 'camelCase',
      },
      preprocessorOptions: {
        scss: {
          additionalData: `@import "@/styles/variables.scss";`,
        },
      },
      postcss: {
        plugins: [
          require('autoprefixer'),
          require('cssnano')({
            preset: 'default',
          }),
        ],
      },
    },

    // ESBuild configuration
    esbuild: {
      drop: isProduction ? ['console', 'debugger'] : [],
      legalComments: 'none',
    },

    // Worker configuration
    worker: {
      format: 'es',
    },
  }
})