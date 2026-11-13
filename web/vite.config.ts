import { resolve } from 'node:path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig(({ mode }) => ({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    proxy: {
      '/api':
        loadEnv(mode, import.meta.dirname, '').API_PROXY_TARGET ??
        'http://localhost:3000',
    },
  },
  build: {
    rolldownOptions: {
      input: {
        main: resolve(import.meta.dirname, 'index.html'),
        diagnostic: resolve(import.meta.dirname, 'diagnostic.html'),
      },
    },
  },
}));
