import { defineConfig } from 'vite';

export default defineConfig({
  root: 'frontend',
  esbuild: { jsx: 'automatic' },
  build: { outDir: '../dist', emptyOutDir: true },
  server: { port: 5188, strictPort: true, proxy: { '/api': process.env.ECOSPLICE_BACKEND_URL || 'http://127.0.0.1:8765' } },
  preview: { proxy: { '/api': process.env.ECOSPLICE_BACKEND_URL || 'http://127.0.0.1:8765' } },
});
