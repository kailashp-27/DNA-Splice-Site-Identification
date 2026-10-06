import { defineConfig } from 'vite';

export default defineConfig({
  root: 'frontend',
  esbuild: { jsx: 'automatic' },
  build: { outDir: '../dist', emptyOutDir: true },
  server: { port: 5173, strictPort: true },
});
